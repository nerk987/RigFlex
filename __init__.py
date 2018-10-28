# ##### BEGIN GPL LICENSE BLOCK #####
#
#  RigFlex.py  -- Quick Soft Body Simulation for Armatures
#  by Ian Huish (nerk)
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# version comment: V0.0.3 main branch - Wobble/Late Parent Fixes

bl_info = {
    "name": "RigFlex",
    "author": "Ian Huish (nerk)",
    "version": (0, 0, 0),
    "blender": (2, 79, 0),
    "location": "Toolshelf>RigFlex",
    "description": "Quick Soft Body Simulation for Armatures",
    "warning": "",
    "category": "Animation"}
    

if "bpy" in locals():
    import imp
    imp.reload(RigFlex)
else:
    from . import RigFlex

import bpy
import mathutils,  math, os
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty, StringProperty
from random import random
from bpy.types import Operator, Panel, Menu
from bl_operators.presets import AddPresetBase
# import shutil




class SBSimMainProps(bpy.types.PropertyGroup):
    sbsim_targetrig = StringProperty(name="Name of the target rig", default="")  
    sbsim_start_frame = IntProperty(name="Simulation Start Frame", default=1)  
    sbsim_end_frame = IntProperty(name="Simulation End Frame", default=250)  
    sbsim_stiffness = FloatProperty(name="stiffness", default=0.5)  
    sbsim_bonelayer = IntProperty(name="Bone Layer", default=24)  
    



class ARMATURE_OT_SBSim_Copy(bpy.types.Operator):
    """Create a new bone layer for soft body simulation"""
    bl_label = "Initialize"
    bl_idname = "armature.sbsim_copy"
    bl_options = {'REGISTER', 'UNDO'}
    
    #update the vertex groups on any associated object
    def UpdateVertexGroups(self, context, targetRig):
        #Get a list of vertex group names to change
        ChangeGroups = []
        for b in targetRig.pose.bones:
            if b.name[-5:] == "_flex":
                ChangeGroups.append(b.name[:-5])
                print("ChangeGroups add: ", b.name[:-5])
        for o in context.scene.objects:
            ArmMod = False
            for mod in o.modifiers:
                if mod.type == 'ARMATURE' and mod.object is not None:
                    if mod.object.name == targetRig.name:
                        print("Object found: ", o.name)
                        ArmMod = True
            for vg in o.vertex_groups:
                if vg.name in ChangeGroups:
                    vg.name = vg.name + "_flex"
            
    

    #Create a new bone layer for soft body simulation    
    def execute(self, context):
        #Get the object
        pFSM = context.scene.SBSimMainProps
        TargetRig = context.object
        selected_bones = []
        if context.selected_pose_bones is not None:
            for b in context.selected_pose_bones:
                print("Selected", b.name)
                selected_bones.append(b.name)
        if TargetRig.type != "ARMATURE":
            print("Not an Armature", context.object.type)
            return  {'FINISHED'}
        TargetRig["SBSim"] = "True"
            
        #Add a copy Transforms constraint at the object level
        
        #delete all non-deform bones
        rig = TargetRig.data
        # context.scene.objects.active = SimRig
        OrigMode = context.mode
        bpy.ops.object.mode_set(mode='EDIT')
        
        #Duplicate each selected bone in Edit mode
        for b in rig.edit_bones:
            print("EditBone", b.name)
            if b.name in selected_bones:
                bsim = rig.edit_bones.new(b.name + "_flex")
                print("New Bone", bsim.name)
                bsim.head = b.head
                bsim.tail = b.tail
                bsim.matrix = b.matrix
                bsim.parent = b.parent

        #Connect the parents of new bones to each other and set correct layer
        for b in rig.edit_bones:
            if b.name[-5:] == "_flex":
                if b.parent is not None:
                    print("BoneIDEdit", b.parent.name)
                    if b.parent.name + "_flex" in rig.edit_bones:
                        b.parent = rig.edit_bones.get(b.parent.name + "_flex", None)
                        print("BoneParentAdd", b.parent.name)
                    else:
                        b.parent = None
                b.layers[pFSM.sbsim_bonelayer] = True
                # b.layers[0] = False
                print("Layer0", b.layers[0])
                for i in range(31):
                    if i != pFSM.sbsim_bonelayer:
                        b.layers[i] = False

                
        #Return from Edit mode
        bpy.ops.object.mode_set(mode=OrigMode)
               
        #Fix up the parents
        
        

        for b in TargetRig.pose.bones:
            print("BoneIDPose", b.name[-5:])
            if b.name[-5:] == "_flex":
                b["Stiffness"] = pFSM.sbsim_stiffness
                crc = b.constraints.new('COPY_TRANSFORMS')
                crc.target = TargetRig
                crc.subtarget = b.name[:-5]
        
        #Update any associated vertex groups
        self.UpdateVertexGroups(context, TargetRig)
        
        return {'FINISHED'}


class ARMATURE_OT_SBSim_Update(bpy.types.Operator):
    """Update the stiffness settings for selected bones"""
    bl_label = "Update"
    bl_idname = "armature.sbsim_update"
    bl_options = {'REGISTER', 'UNDO'}
    

    #Update the simulated armature settings    
    def execute(self, context):

        pFSM = context.scene.SBSimMainProps

        if context.selected_pose_bones is not None:
            for b in context.selected_pose_bones:
                b["Stiffness"] = pFSM.sbsim_stiffness
                
        return {'FINISHED'}

        
    

class ARMATURE_PT_SBSim(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "SBSim"
    bl_idname = "armature.sbsim"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "RigFlex"
    


    @classmethod
    def poll(cls, context):
        if context.object != None:
            return (context.mode in {'OBJECT', 'POSE'}) and (context.object.type == "ARMATURE")
        else:
            return False

    def draw(self, context):
        layout = self.layout

        obj1 = context.object
        scene = context.scene
        
        box = layout.box()
        box.label("Main")
        box.prop(scene.SBSimMainProps, "sbsim_start_frame")
        box.prop(scene.SBSimMainProps, "sbsim_end_frame")
        box.operator("armature.sbsimulate")
        box.operator("armature.sbsim_unbake")
        box = layout.box()
        box.label("Initial Setup")
        box.operator("armature.sbsim_copy")
        box.prop(scene.SBSimMainProps, "sbsim_stiffness")
        box.prop(scene.SBSimMainProps, "sbsim_bonelayer")
        box = layout.box()
        box.label("Update")
        box.operator("armature.sbsim_update")
        box.prop(scene.SBSimMainProps, "sbsim_stiffness")
        box = layout.box()
        box.label("Remove")
        box.operator("armature.sbsim_revert")


def register():
    bpy.utils.register_class(SBSimMainProps)
    bpy.types.Scene.SBSimMainProps = bpy.props.PointerProperty(type=SBSimMainProps)
    from . import RigFlex
    RigFlex.registerTypes()
    bpy.utils.register_class(ARMATURE_PT_SBSim)
    # bpy.utils.register_class(ARMATURE_OT_SBSim_Run)
    bpy.utils.register_class(ARMATURE_OT_SBSim_Copy)
    bpy.utils.register_class(ARMATURE_OT_SBSim_Update)
    


def unregister():
    del bpy.types.Scene.SBSimMainProps
    bpy.utils.unregister_class(SBSimMainProps)
    from . import RigFlex
    RigFlex.unregisterTypes()
    bpy.utils.unregister_class(ARMATURE_PT_SBSim)
    # bpy.utils.unregister_class(ARMATURE_OT_SBSim_Run)
    bpy.utils.unregister_class(ARMATURE_OT_SBSim_Copy)
    bpy.utils.unregister_class(ARMATURE_OT_SBSim_Update)


if __name__ == "__main__":
    register()
