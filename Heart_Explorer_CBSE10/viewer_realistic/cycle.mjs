// Illustrative cycle timing, not a clinical simulation.
export function cardiacCycle(p){
 p=((p%1)+1)%1;
 const atrial=p>=.18&&p<.36, ejection=p>=.42&&p<.72;
 const avOpen=p<.36||p>=.78;
 const ventricular=p>=.36&&p<.78?Math.sin((p-.36)/.42*Math.PI):0;
 return {avOpen,outletOpen:ejection,atrial:atrial?Math.sin((p-.18)/.18*Math.PI):0,ventricular,
 fillProgress:p>=.78?(p-.78)/.58:(p+.22)/.58,
 ejectProgress:(p-.42)/.30,
 title:atrial?'Atria squeeze':p>=.36&&p<.42?'Ventricles build pressure':ejection?'Ventricles pump blood out':p>=.72&&p<.78?'Ventricles relax':'Heart fills',
 explanation:atrial?'The atria push the last part of their blood through the open tricuspid and mitral valves into the ventricles.':p>=.36&&p<.42?'Both sets of valves are closed briefly as ventricular pressure rises.':ejection?'The right ventricle sends blood to the lungs through the pulmonary artery. The left sends blood to the body through the aorta.':p>=.72&&p<.78?'The outlet valves close to prevent backflow. Both sets of valves are briefly closed.':'Blood returns from the body to the right atrium and from the lungs to the left atrium, then flows through the open inlet valves into the ventricles.'};
}
