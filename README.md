# RigFlex - Simple Soft Body for Armatures

V0.3.2 Initial Blender 2.8 - multi armature bug fix and freeze options

Addon Download : [RigFlex.zip](https://github.com/nerk987/RigFlex/releases/download/v0.3.0/RigFlex.zip) 

# 1.0 Introduction
The movement of many animated characters is improved by some sort of soft body simulation. Antennas, clothing, tails, feathers, scales - you name it. Blender has a variety of techniques for this, often using soft body or cloth simulation applied to a lattice or mesh which in turn is applied to the cahracter mesh via modifiers. It's very flexible and powerful, but take some effort to set up.

However, there is no soft body for armatures, and often an acurate simulation is not the goal, just a simple first order lag to the movement of some of the mesh. The RigFlex addon aims to make this a simple process. 

# 2.0 Installation

Download the RigFlex.zip file, install and enable in the usual way.

# 3.0 Usage

## 3.1 Quick Start

Briefly, you animate your rig however you want. When your're done, in Pose mode, select the deform bones that require a 'soft body' action. Locate the RigFlex tab in the Toolshelf to the left. In the 'Initial Setup' panel, click on the 'Initialize' button. The bones you had selected are duplicated to the bone layer shown in the same panel, and any meshes which have an assocoiated armature modifier or parent are updated to those bones if required. Then in the 'Main' panel, set the start and end frames to be baked, and press the 'Bake' button.

The addon adds keyframes for the bones you originally selected over the start to end frames. These bones should now have a soft body look. 

To change the animation, click on the 'Free Bake' button and the new bones will be track the original bones. Modify the animation on the original rig, then hit the 'Bake' button again. Once again the soft body action will be baked to the new bone layer.

The armature and associated meshes can be returned to their original state if you want to start over, or just want to remove the effects of the addon. Use the 'Revert' button in the 'Removal' panel.

## 3.2 Changing the 'Stiffness'
The soft body algorithm for this addon is purposely kept very simple, and acts as a heavily damped spring system. A stiffness of 1.0 will result in an exact copy. With a stiffness of 0.5, the simulated bone will move around halfway towards the original bone's location each scan. A stiffness of 0.1 will be very floppy. There should be no overshoot unless movements are very extreme.

When the soft body layer is first initialized, each new deform bone is assigned a 'Stiffness' to a custom bone property. The deform bones are assigned a stiffness  based on the stiffness property (0.5 by default). This can be adjusted using the 'Update' button in the update panel. Select the bones you want to change from the soft body bone layer (not the orginal bones), set the required stiffness, and click on 'Update'. You can repeat this as often as you need.  The stiffness value can also be changed directly in the custom properties area of the bone tab.

When you're done, click on the bake button.

## 3.3 Freeze and Unfreeze
If you are working on more complex models, it might be helpful to work on one part of the model at a time. For example, while animating an elephant, you've added rig flex to the tail, baked the action and then tweaked it a little. It's working just how you like. Now you'd like to give the trunk a bit more character. You can select the bones in the tail (either the original deform bones, or the added rigflex bones) and click the 'Freeze' button. The keyframes already baked will not be affected until the 'Unfreeze' command is selected. You can 'Initialize' the deform bones in the trunk, and work on that without the keyframes in the tail being recalculated.

The 'Unfreeze' button will unfreeze all rigflex bones in the model - not just the selected ones.

## 3.4 More complex rigs like Rigify and BlenRig
This addon was intended to provide a simple soft body feel to a few bones in a chain. It may by possible to use it for more wide ranging purposes, but there are a few issues. In many rigs - such as rigify and blenrig - when only the deform bones are retained in the 'sim' bone layer, some parenting information is lost. For example the upper arm deform bone is unlikely to be parented directly to a spine bone (this is done via organisational bones). In this case if both the spine and the arm bones are given a stiffness less than 1.0, things won't work right because the arm bone in the sim rig will copy the location of the arm bone in the original rig rather than following the soft body motion of the spine. As a work around, you can manually parent the arm bone in the sim bone layer to the shoulder/spine bone in the sim rig, etc, etc. Then bake again and it may do what you want! Other common parenting links required are fingers to palm bones, palm bones to wrist, and facial bones to head.



