// Each lesson has a concrete atom demonstration and a question to investigate.
const step=(label,counts,explanation,focus)=>({label,counts,explanation,focus});
export const guides={
 atom:{title:'What is an atom?',steps:[
  step('A helium atom',[2,2,2],'This whole model represents one helium-4 atom: a nucleus with 2 protons and 2 neutrons, surrounded by 2 electrons. The atom is neutral because its positive and negative charges balance.','nucleus'),
  step('A different element',[6,6,6],'This is one carbon-12 atom, not a molecule. Six protons identify carbon. A molecule contains atoms bonded together; this explorer displays one atom at a time.','proton')],question:'Which count distinguishes helium from carbon?'},
 structure:{title:'Structure of an atom',steps:[
  step('Find the centre',[2,2,2],'The labelled nucleus is the centre. Red protons and gold neutrons account for almost all atomic mass. Use Spread nucleus to count them separately.','nucleus'),
  step('Look outside',[2,2,2],'The blue electrons occupy the region outside the nucleus. K is the first shell. The nucleus is drawn much larger than its real proportion so you can inspect it.','shell')],question:'Where are the electrons, and where is most of the mass?'},
 proton:{title:'Protons',steps:[
  step('Six protons',[6,6,6],'The red + particles are protons. Six protons identify carbon, with atomic number Z = 6. Each proton has charge +1.','proton'),
  step('Seven protons',[7,6,6],'Changing only protons from 6 to 7 changes the element to nitrogen. Electrons stayed at 6, so this counting example also has charge +1. This is a hypothetical nuclear change, not an ordinary chemical reaction.','proton')],question:'Why did both the element name and electric charge change?'},
 neutron:{title:'Neutrons',steps:[
  step('Carbon-12',[6,6,6],'The gold 0 particles are neutrons. Carbon-12 has 6 protons plus 6 neutrons. Neutrons have mass, despite having no electric charge.','neutron'),
  step('Carbon-13',[6,7,6],'One more neutron makes carbon-13. The mass number increases to 13. It is still neutral carbon: its protons and electrons have not changed.','neutron')],question:'Which two quantities stay unchanged when we add a neutron?'},
 electron:{title:'Electrons',steps:[
  step('Neutral sodium',[11,12,11],'The blue − particles are electrons. Eleven electrons balance eleven protons, giving total charge zero.','electron'),
  step('Sodium ion',[11,12,10],'One electron has been removed: 11 − 10 = +1. The nucleus is unchanged, so this is still sodium-23.','electron')],question:'Why does losing a negative particle make the ion positive?'},
 atomic_number:{title:'Atomic number',steps:[
  step('Read Z',[8,8,8],'Z = 8 counts the eight protons. This identifies oxygen. Mass number A = 16 also includes the eight neutrons.','proton'),
  step('Same Z, different charge',[8,8,10],'O²⁻ still has Z = 8. Its ten electrons do not change its element identity. Z equals electron count only for a neutral atom.','proton')],question:'For this ion, does Z equal 8, 10 or 16?'},
 mass_number:{title:'Mass number',steps:[
  step('Add the nucleons',[8,8,8],'A = protons + neutrons = 8 + 8 = 16. Spread the nucleus to see the two kinds of nucleon. Electrons are not included in A.','nucleus'),
  step('Two extra neutrons',[8,10,8],'A is now 8 + 10 = 18: oxygen-18. Z remains 8. To find neutrons, subtract Z from A: 18 − 8 = 10.','neutron')],question:'Would removing an electron change A?'},
 counting:{title:'Counting particles',steps:[
  step('Read sodium notation',[11,12,10],'Read A = 23, Z = 11 and charge +1. Protons = 11. Neutrons = 23 − 11 = 12. Electrons = 11 − 1 = 10. Check these against the labelled model.','nucleus'),
  step('Try a negative ion',[8,8,10],'For oxygen-16 with charge 2−: protons = 8; neutrons = 16 − 8 = 8; electrons = 8 + 2 = 10. A negative charge means extra electrons.','electron')],question:'Why do we add two when counting electrons in O²⁻?'},
 isotopes:{title:'Isotopes',steps:[
  step('Carbon-12',[6,6,6],'First isotope: Z = 6, A = 12. There are six protons and six neutrons. Compare the next example while watching the gold particles.','neutron'),
  step('Carbon-13',[6,7,6],'Second isotope: the proton count is still six, but there are seven neutrons. Same Z and different A means isotopes of carbon.','neutron'),
  step('Carbon-14',[6,8,6],'Carbon-14 has eight neutrons. It is radioactive; carbon-12 and carbon-13 are stable. Not every isotope is radioactive, and this model does not simulate decay.','neutron')],question:'What do all three examples share?'},
 isobars:{title:'Isobars',steps:[
  step('Carbon-14',[6,8,6],'Count 6 protons + 8 neutrons = 14 nucleons. Remember A = 14 before switching to nitrogen.','nucleus'),
  step('Nitrogen-14',[7,7,7],'Now 7 protons + 7 neutrons = 14 nucleons. The mass number matches carbon-14, but the element differs. This pair are isobars, not isotopes.','nucleus')],question:'Which stays the same: A or Z?'},
 shells:{title:'Electron shells and valency',steps:[
  step('Sodium: K, L, M',[11,12,11],'Follow the labels: K is the innermost shell with 2 electrons; L has 8; M is the outermost with 1. The single M-shell electron is a valence electron. Sodium commonly loses it, giving valency 1.','shell'),
  step('Oxygen: valency 2',[8,8,8],'K has 2 electrons and L has 6. L is the outermost occupied shell, so oxygen has 6 valence electrons. Its usual valency is 2: it commonly gains two electrons or shares in two bonds.','shell'),
  step('Calcium: K, L, M, N',[20,20,20],'The school arrangement is K: 2, L: 8, M: 8, N: 2. N is now outermost. Calcium has 2 valence electrons and a usual valency of 2. This first-20-elements pattern is not a universal shell-filling rule.','shell')],question:'Why can valency differ from the number of valence electrons?'},
 ions:{title:'Ions',steps:[
  step('Neutral sodium',[11,12,11],'Eleven protons balance eleven electrons. The atom has charge zero. Watch what happens when one electron is removed.','electron'),
  step('Positive ion Na⁺',[11,12,10],'Now protons − electrons = 11 − 10 = +1. This positive ion is a cation. Its mass number and element identity did not change.','electron'),
  step('Negative ion Cl⁻',[17,18,18],'This separate example has 17 protons and 18 electrons, so charge = −1. It is an anion. Solid table salt already contains Na⁺ and Cl⁻; dissolving salt separates existing ions.','electron')],question:'Which particle must change to make an ion without changing its element?'},
 revision:{title:'Practice and revision',steps:[
  step('Solve Mg²⁺',[12,12,10],'For magnesium-24 with charge 2+: Z = 12, A = 24. Predict all three particle counts, then check the readout: p = 12, n = 12, e = 10.','nucleus'),
  step('Identify the change',[12,13,10],'Only the neutron count increased. The model now shows magnesium-25 with the same +2 charge. It is a different isotope, not a different element.','neutron'),
  step('Neutral again',[12,13,12],'Two electrons were added. The atom is neutral magnesium-25. Z and A did not change. Explain each change to the tutor in your own words.','electron')],question:'Can you explain element, isotope and charge using p, n and e?'}
};
