# ##### BEGIN GPL LICENSE BLOCK #####
#
#  RigFlex.py  -- a script 
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

import bpy
import mathutils,  math, os
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty, BoolProperty, EnumProperty, StringProperty
from random import random

#Misc Rountines
def PrintMatrix(mat, desc):
    ret = mat.decompose()
    print(desc)
    print("Trans: ", ret[0])
    print("Rot: (%.2f, %.2f, %.2f), %.2f" % (ret[1].axis[:] + (math.degrees(ret[1].angle), )))  

def PrintQuat(quat, desc):
    print(desc)
    print("Rot: (%.2f, %.2f, %.2f), %.2f" % (quat.axis[:] + (math.degrees(quat.angle), )))  


    
class ARMATURE_OT_SBSimulate(bpy.types.Operator):
    """Bake the soft body simulation"""
    bl_idname = "armature.sbsimulate"
    bl_label = "Bake"
    bl_options = {'REGISTER', 'UNDO'}
    
    sTargetRig = None
    sSourceRig = None
    sTree = []
    # sBase = None
    # sTestTarg = None
    # sTestSource = None
    sOldTail = {}
    sPrevTail = {}
    sBone = None
    sNode = []
    
    def Redirect(self, simRig, targetRig, Dirn, context):

        if Dirn:
            old = targetRig
            new = simRig
        else:
            new = targetRig
            old = simRig
        for o in context.scene.objects:
            if o.parent == old:
                loc = o.matrix_world.translation
                o.parent = new
                o.matrix_world.translation = loc
            for mod in o.modifiers:
                if mod.type == 'ARMATURE' and mod.object is not None:
                    if mod.object.name == old.name:
                        mod.object = new

    def addBranch(self, bones, Branch, CurrentBone):
        children = []
        for b in bones:
            if b.parent == CurrentBone:
                children.append(b)

        if len(children) > 1:
            for c in children:
                newBranch = [c]
                self.sTree.append(newBranch)
                self.addBranch(bones, newBranch, c)
        elif len(children) == 1:
            Branch.append(children[0])
            self.addBranch(bones, Branch, children[0])


    def BuildTree(self, TargetRig):
        self.sTree = []
        for b in TargetRig.pose.bones:
            if b.parent == None:
                Branch = [b]
                self.sTree.append(Branch)
                self.addBranch(TargetRig.pose.bones, Branch, b)
    
    
    def SetInitialKeyframe(self, TargetRig, nFrame):
        TargetRig.keyframe_insert(data_path='location',  frame=(nFrame))
        TargetRig.keyframe_insert(data_path='rotation_euler',  frame=(nFrame))

    
    def RemoveKeyframes(self, armature, bones):
        dispose_paths = []
        for bone in bones:
            dispose_paths.append('pose.bones["{}"].rotation_quaternion'.format(bone.name))
            dispose_paths.append('pose.bones["{}"].scale'.format(bone.name))
        dispose_curves = [fcurve for fcurve in armature.animation_data.action.fcurves if fcurve.data_path in dispose_paths]
        for fcurve in dispose_curves:
            armature.animation_data.action.fcurves.remove(fcurve)

    #Set up the parameter for the iteration in ModalMove        
    def BoneMovement(self, context):
        
        scene = context.scene
        pFSM = scene.SBSimMainProps
        startFrame = pFSM.sbsim_start_frame
        endFrame = pFSM.sbsim_end_frame
        TargetRig = self.sTargetRig
        self.BuildTree(TargetRig)
       

        #Go back to the start before removing keyframes to remember starting point
        context.scene.frame_set(startFrame)
       
        #Delete existing keyframes
        try:
            self.RemoveKeyframes(TargetRig, TargetRig.pose.bones)
        except AttributeError:
            pass
        
        #record to previous tail position
        context.scene.frame_set(startFrame)
        context.scene.update()
        # self.SetInitialKeyframe(TargetRig, startFrame)
        
    def ModalMove(self, context):
        scene = context.scene
        pFSM = scene.SBSimMainProps
        startFrame = pFSM.sbsim_start_frame
        endFrame = pFSM.sbsim_end_frame
        context.scene.update()
        
        nFrame = scene.frame_current
        # print("Frame: ", nFrame)
        
        #Get the conditions for the whole armature
        WT_Mat = self.sTargetRig.matrix_world
        WT_Mat_Inv = WT_Mat.inverted_safe()
        
        #Handle each bone
        for branch in self.sTree:

            #For each bone in the branch
            for BranchBone in branch:
            
                if nFrame == startFrame:
                    self.sOldTail[BranchBone.name] = WT_Mat * BranchBone.tail
                    SourceBone = self.sSourceRig.pose.bones.get(BranchBone.name)
                    if SourceBone is None:
                        print("Null Source Bone: ", BranchBone.name)
                    BranchBone.matrix = SourceBone.matrix
                else:

                    context.scene.update()

                    BranchBone.rotation_mode = 'QUATERNION'
                        
                    #Do initial calcs in world co-ords    
                    TailLoc = WT_Mat * BranchBone.tail
                    if BranchBone.parent is None:# or nFrame == startFrame:
                        HeadLoc = WT_Mat * BranchBone.head
                    else:
                        HeadLoc = self.sOldTail[BranchBone.parent.name]
                    Movement = TailLoc - self.sOldTail[BranchBone.name]
                    VecBeforeMove = TailLoc - HeadLoc
                    VecAfterMove = self.sOldTail[BranchBone.name] - HeadLoc
                    RotMove = VecBeforeMove.rotation_difference(VecAfterMove)
                    
                    # #print
                    # if "Bone.001" in BranchBone.name:
                        # print("T, OT, H", TailLoc, self.sOldTail[BranchBone.name], HeadLoc)
                    
                    # Now convert rotation to the local bone co-ords
                    bm = BranchBone.matrix.to_3x3()
                    bm.invert()
                    NewRotAxis = bm * RotMove.axis
                    RotMoveLocal = mathutils.Quaternion(NewRotAxis, RotMove.angle)
                    
                    # Add spring function
                    SourceBone = self.sSourceRig.pose.bones.get(BranchBone.name)
                    if SourceBone is None:
                        print("Null Source Bone: ", BranchBone.name)
                    NewAngle = BranchBone.rotation_quaternion.copy()
                    NewAngle.rotate(RotMoveLocal)
                        
                    # #print
                    # if "Bone.001" in BranchBone.name:
                        # PrintQuat(SourceBone.rotation_quaternion, "SourceQuat")
                        # PrintQuat(NewAngle, "NewAngle")
                        
                    #Work out Source Bone rotation after constraints (rotation_quaternion doesn't seem to work)
                    if BranchBone.parent is not None and SourceBone.parent is not None:
                        #Rest position inverse relationship
                        edit2parent_i = (BranchBone.parent.bone.matrix_local.inverted() * BranchBone.bone.matrix_local).inverted()
                        
                        #Armature Pose relationship
                        final2parent = SourceBone.parent.matrix.inverted() * SourceBone.matrix
                        
                        #Desired move in pose space
                        pspacemove = edit2parent_i * final2parent

                        SourceQuat = pspacemove.to_quaternion()
                    else:
                        SourceQuat = (SourceBone.bone.matrix_local.inverted() * SourceBone.matrix).to_quaternion()
                        # print("ml:", SourceQuat.to_euler())

                    if "Stiffness" in BranchBone:
                        NewAngle = NewAngle.slerp(SourceQuat, BranchBone["Stiffness"])
                    else:
                        NewAngle = NewAngle.slerp(SourceQuat, pFSM.sbsim_stiffness)
                    # if nFrame > startFrame:
                    BranchBone.rotation_quaternion = NewAngle
                BranchBone.keyframe_insert(data_path='rotation_quaternion',  frame=(nFrame))
                context.scene.update()
                # if "DEF-FeelerT.002.R" in BranchBone.name:
                    # PrintQuat(BranchBone.rotation_quaternion, "BoneAngle")
                
                self.sPrevTail[BranchBone.name] = BranchBone.tail
                self.sOldTail[BranchBone.name] = WT_Mat * BranchBone.tail
        
                #Diagnostics
                # print("TailLoc: (SimRig Tail)")
                # print(TailLoc)
                # print("HeadLoc: (SimRig Head)")
                # print(HeadLoc)
                # if "001" in SourceBone.name or "004" in SourceBone.name:
                    # print("SourceBone", SourceBone.name)
                    # PrintQuat(SourceBone.rotation_quaternion, "SourceQuat")
                # NewQuat = SourceBone.matrix.to_quaternion()
                # PrintQuat(NewQuat, "NewQuat")
                
        #Go to next frame, or finish
        wm = context.window_manager
        if nFrame == endFrame:
            print("Finished")
            return 0
        else:
            wm.progress_update(nFrame*99.0/endFrame)
            context.scene.frame_set(nFrame + 1)
            # print("Increment Frame")
            return 1
        

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            modal_rtn = self.ModalMove(context)
            if modal_rtn == 0:
                context.scene.frame_set(context.scene.SBSimMainProps.sbsim_start_frame)
                print("Cancelled")
                wm = context.window_manager
                wm.progress_end()
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        sFPM = context.scene.SBSimMainProps
        
        if "SBSim" not in context.object and "SBSource" in context.object:
            self.sTargetRig = context.object
            self.sSourceRig = context.scene.objects.get(context.object["SBSource"])
            print("Option 1")
        elif "SBSim" in context.object and context.object["SBSim"] in context.scene.objects:
            self.sSourceRig = context.object
            self.sTargetRig = context.scene.objects.get(context.object["SBSim"])
            context.scene.objects.active = self.sTargetRig
            print("Option 2")
        else:
            bpy.ops.armature.sbsim_copy()
            context.scene.update()
            
            self.sTargetRig = context.object
            self.sSourceRig = context.scene.objects.get(context.object["SBSource"])
            print("Option 3")
        
        print ("Current Name: ", context.object.name)
        context.scene.update()

        #Convert dependent objects
        context.scene.frame_set(sFPM.sbsim_start_frame)
        self.Redirect(self.sTargetRig, self.sSourceRig, True, context)
            
        scene = context.scene
        bpy.data.objects[self.sSourceRig.name].select = False
        
        #Delete any unnecessary constraints
        for b in self.sTargetRig.pose.bones:
            if "Stiffness" in b:
                if b["Stiffness"] < 1.0 and b.parent is not None:
                    for c in b.constraints:
                        b.constraints.remove(c)
        
        #Progress bar
        wm = context.window_manager
        wm.progress_begin(0.0,100.0)

        scene.frame_set(sFPM.sbsim_start_frame)
        self.BoneMovement(context) 
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.001, context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

class ARMATURE_OT_SBSim_Revert(bpy.types.Operator):
    """Revert to the original armature"""
    bl_label = "Revert"
    bl_idname = "armature.sbsim_revert"
    bl_options = {'REGISTER', 'UNDO'}
    
    
    def Redirect(self, simRig, targetRig, Dirn, context):
    
        if Dirn:
            old = targetRig
            new = simRig
        else:
            new = targetRig
            old = simRig
        for o in context.scene.objects:
            if o.parent == old:
                loc = o.matrix_world.translation
                o.parent = new
                o.matrix_world.translation = loc
            for mod in o.modifiers:
                if mod.type == 'ARMATURE':
                    if mod.object.name == old.name:
                        mod.object = new

    #revert to the original amature    
    def execute(self, context):
        sFPM = context.scene.SBSimMainProps
       
        if "SBSim" not in context.object and "SBSource" in context.object:
            self.sTargetRig = context.object
            self.sSourceRig = context.scene.objects.get(context.object["SBSource"])
        elif "SBSim" in context.object and context.object["SBSim"] in context.scene.objects:
            self.sSourceRig = context.object
            self.sTargetRig = context.scene.objects.get(context.object["SBSim"])
            context.scene.objects.active = self.sSourceRig

        context.scene.frame_set(sFPM.sbsim_start_frame)
        
        if self.sSourceRig is not None and self.sTargetRig is not None:
            self.Redirect(self.sTargetRig, self.sSourceRig, False, context)
        context.scene.objects.active = self.sSourceRig

        
        return {'FINISHED'}

class ARMATURE_OT_SBSim_Test(bpy.types.Operator):
    """Test"""
    bl_label = "Test"
    bl_idname = "armature.sbsim_test"
    bl_options = {'REGISTER', 'UNDO'}
    
    
    def execute(self, context):
        sim = bpy.data.objects["Armature"]
        sb = sim.pose.bones["Bone.001"]
        test = bpy.data.objects["test"]
        tb = test.pose.bones["Bone"]
        tb1 = test.pose.bones["Bone.001"]
        
        tbr = tb.bone.matrix_local
        tb1r = tb1.bone.matrix_local
        tbri = tb.bone.matrix_local.inverted()
        tb1ri = tb1.bone.matrix_local.inverted()
        
        sbm = sb.matrix
        sbmi = sbm.inverted()
        sbpm = sb.parent.matrix
        sbpmi = sbpm.inverted()
        
        tbmi = tb.matrix.inverted()        
        tbm = tb.matrix        
        tb1mi = tb1.matrix.inverted()        
        tb1m = tb1.matrix        
        
        
        #Test Edit inverse relationship
        edit2parent = (tbri * tb1r)
        edit2parent_i = (tbri * tb1r).inverted()
        print("EditRot", edit2parent_i.to_euler())
        
        #Armature Pose relationship
        final2parent = sbpmi * sbm
        print("PoseRot", final2parent.to_euler())
        
        #Desired move in pose space
        pspacemove = edit2parent_i * final2parent
        print("pspacemove", pspacemove.to_euler())
        
        tb1.rotation_quaternion = pspacemove.to_quaternion()
        
        loc = tbri * sb.parent.matrix.translation
        tb.location = loc
        

        
        return {'FINISHED'}
        

def registerTypes():
    bpy.utils.register_class(ARMATURE_OT_SBSimulate)
    bpy.utils.register_class(ARMATURE_OT_SBSim_Revert)
    bpy.utils.register_class(ARMATURE_OT_SBSim_Test)

def unregisterTypes():
    bpy.utils.unregister_class(ARMATURE_OT_SBSimulate)
    bpy.utils.unregister_class(ARMATURE_OT_SBSim_Revert)
    bpy.utils.unregister_class(ARMATURE_OT_SBSim_Test)


if __name__ == "__main__":
    register()

