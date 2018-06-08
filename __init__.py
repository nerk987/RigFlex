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

# version comment: V0.0.2 main branch - Object location fix

bl_info = {
    "name": "RigFlex",
    "author": "Ian Huish (nerk)",
    "version": (0, 0, 0),
    "blender": (2, 78, 0),
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
    



class ARMATURE_OT_SBSim_Copy(bpy.types.Operator):
    """Create a new armature for simulation"""
    bl_label = "Copy"
    bl_idname = "armature.sbsim_copy"
    bl_options = {'REGISTER', 'UNDO'}
    

    #Copy the Source rig to a new armature    
    def execute(self, context):
        #Get the object
        pFSM = context.scene.SBSimMainProps
        TargetRig = context.object
        selected_bones = []
        if context.selected_pose_bones is not None:
            for b in context.selected_pose_bones:
                selected_bones.append(b)
        if TargetRig.type != "ARMATURE":
            print("Not an Armature", context.object.type)
            return  {'FINISHED'}
        SimRig = TargetRig.copy()
        SimRig.name = TargetRig.name + "_sbsim"
        SimRig.data = TargetRig.data.copy()
        SimRig.data.name = TargetRig.data.name + "_sbsim"
        context.scene.objects.link(SimRig)
        TargetRig["SBSim"] = SimRig.name
        SimRig["SBSource"] = TargetRig.name
        if "SBSim" in SimRig:
            del SimRig["SBSim"]
            
        #Add a copy Transforms constraint at the object level
        
            
        #delete all non-deform bones
        rig = SimRig.data
        context.scene.objects.active = SimRig
        OrigMode = context.mode
        bpy.ops.object.mode_set(mode='EDIT')
        #delete constraints
        for b in SimRig.pose.bones:
            for c in b.constraints:
                b.constraints.remove(c)
                
        #remove parents that aren't deform bones
        for b in rig.edit_bones:
            if b.parent is not None:
                if not b.parent.use_deform:
                    b.parent = None
        
        for b in rig.edit_bones:
            if not b.use_deform:
                rig.edit_bones.remove(b)
        
        # Remove animation data
        bpy.ops.object.mode_set(mode=OrigMode)
        if SimRig.animation_data is not None:
            SimRig.animation_data.action = None
        
        # #Hide the active layer
        # SimRig.data.layers[1] = True
        # SimRig.data.layers[0] = False
        
        #Add copy transforms constraint to all bones with no parent
        crco = SimRig.constraints.new('COPY_TRANSFORMS')
        crco.target = TargetRig
        
        #Delete any unnecessary constraints
        for b in SimRig.pose.bones:
            for c in b.constraints:
                b.constraints.remove(c)

        for b in SimRig.pose.bones:
            SourceBone = TargetRig.pose.bones.get(b.name)
            if SourceBone is not None:
                if SourceBone not in selected_bones:
                    # print("SourceBone not Selected", b.name)
                    crc = b.constraints.new('COPY_TRANSFORMS')
                    crc.target = TargetRig
                    crc.subtarget = SourceBone.name
                    # print("CRC Sub:", crc.subtarget)
                    b["Stiffness"] = 1.0
                elif b.parent is None:
                    # print("SourceBone no Parent", b.name)
                    b["Stiffness"] = pFSM.sbsim_stiffness
                    crc = b.constraints.new('COPY_LOCATION')
                    crc.target = TargetRig
                    crc.subtarget = SourceBone.name
                else:
                    # print("SourceBone Selected", b.name)
                    b["Stiffness"] = pFSM.sbsim_stiffness
                    
        
        
        return {'FINISHED'}


class ARMATURE_OT_SBSim_Update(bpy.types.Operator):
    """Update the armature settings"""
    bl_label = "Update"
    bl_idname = "armature.sbsim_update"
    bl_options = {'REGISTER', 'UNDO'}
    

    #Update the simulated armature settings    
    def execute(self, context):

        pFSM = context.scene.SBSimMainProps
        selected_bones = []

        if "SBSim" not in context.object and "SBSource" in context.object:
            SimRig = context.object
            TargetRig = context.scene.objects.get(context.object["SBSource"])
        elif "SBSim" in context.object and context.object["SBSim"] in context.scene.objects:
            TargetRig = context.object
            SimRig = context.scene.objects.get(context.object["SBSim"])
        else:
            print("Sim rig not found", context.object.type)
            return  {'FINISHED'}
            
        if context.selected_pose_bones is not None:
            # print("Context Object: ", context.object.name)
            for b in context.selected_pose_bones:
                selected_bones.append(b.name)
                
        for b in SimRig.pose.bones:
            # print("Bone Name: ", b.name)
            bTarg = TargetRig.pose.bones.get(b.name)
            if bTarg is not None:
                if bTarg.name in selected_bones:
                    b["Stiffness"] = pFSM.sbsim_stiffness
                    if pFSM.sbsim_stiffness < 1.0 and b.parent is not None:
                        #Delete any unnecessary constraints
                        for c in b.constraints:
                            b.constraints.remove(c)
        
        
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
        box.operator("armature.sbsim_revert")
        box = layout.box()
        box.label("Settings")
        box.prop(scene.SBSimMainProps, "sbsim_stiffness")
        box.operator("armature.sbsim_update")
        box = layout.box()
        box.operator("armature.sbsim_test")

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

