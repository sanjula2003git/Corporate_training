"""Original school-level teaching notes; see SOURCES.md for curriculum context."""
SOURCE = 'https://ncert.nic.in/textbook.php'

def lesson(id, title, subtitle, text, points, example, misconception, question, options, answer, why):
    return dict(id=id,title=title,subtitle=subtitle,text=text,points=points,example=example,
                misconception=misconception,question=question,options=options,answer=answer,why=why)

LESSONS = [
lesson('atom','What is an atom?','Begin with the building blocks of matter.',
'''An **atom** is the smallest unit of an element that retains its chemical identity. A piece of copper contains a huge number of copper atoms. Each copper atom has the same number of protons, even though its neutron count can vary.

Atoms can join to make **molecules**. A water molecule contains two hydrogen atoms and one oxygen atom: H₂O. Water is a compound, not an element. Some substances, such as sodium chloride, form extended arrangements of ions rather than separate molecules.

An atom is very small, but it has internal structure. We will use enlarged diagrams to explore it; these diagrams are models, not photographs.''',
['An element contains atoms with one particular proton number.','Atoms can combine to form substances.','An atom contains smaller particles.'],
'In H₂O, the small 2 means two hydrogen atoms. There is one oxygen atom in each water molecule.',
'An atom and a molecule are not the same thing.',
'How many atoms are in one water molecule?',['2','3','4'],1,'H₂O contains two hydrogen atoms and one oxygen atom: three in total.'),
lesson('structure','Structure of an atom','A tiny nucleus and the region around it.',
'''The **nucleus** is the tiny central part of an atom. It contains protons and, in most atoms, neutrons. Almost all the atom’s mass is concentrated here. Ordinary hydrogen-1 is an important exception: its nucleus is one proton with no neutron.

**Electrons** occupy the region around the nucleus. School diagrams often show them on shells to explain energy levels and electron counts. Real electrons do not follow the neat circular tracks of little planets.

The nucleus is much smaller than the atom. Our pictures enlarge the nucleus and particles so you can select and count them. A diagram with large touching spheres is a teaching aid, not the atom’s literal appearance.''',
['The nucleus contains protons and usually neutrons.','Electrons occupy the space around the nucleus.','Most atomic mass is in the nucleus.'],
'Helium-4 has two protons and two neutrons in its nucleus, with two electrons around it when neutral.',
'The nucleus is not as large a fraction of a real atom as it appears in our diagram.',
'Where is most of an atom’s mass?',['In the nucleus','In the electrons','Equally everywhere'],0,'Protons and neutrons are much heavier than electrons and are located in the nucleus.'),
lesson('proton','Protons','The positive particle that identifies an element.',
'''A **proton** has a relative electric charge of **+1** and a mass of approximately **1 u**. Here, u is the unified atomic mass unit. Protons are in the nucleus.

The number of protons determines which element an atom belongs to. Every carbon nucleus contains six protons; every oxygen nucleus contains eight. This number is called the **atomic number**, Z.

Changing the number of protons changes the element. It is not how ordinary chemical reactions work: those involve changes in electrons and bonding, while the nuclei keep their element identities.''',
['Charge: +1.','Location: nucleus; approximate mass: 1 u.','Proton number determines the element.'],
'A nucleus with 6 protons is carbon. If the proton count becomes 7, the element is nitrogen, regardless of the neutron count.',
'Adding a proton is a nuclear change, not the way an atom becomes a positive ion.',
'An atom has 8 protons. What identifies it as oxygen?',['Its neutron count','Its proton count','Its electron mass'],1,'The element is defined by its eight protons.'),
lesson('neutron','Neutrons','No electric charge, but an important role.',
'''A **neutron** has **zero electric charge** and a mass of approximately **1 u**, slightly more than a proton. Neutrons are found in the nucleus of most atoms.

Neutrons contribute to nuclear mass and to the interactions that bind nuclei. They do not cancel the positive electric charge of protons. Whether a nucleus is stable depends on its combination of protons and neutrons; adding more neutrons does not always make it more stable.

Atoms with the same proton number but different neutron numbers are **isotopes**. Carbon-12 has six neutrons, while carbon-14 has eight. Both are carbon because each has six protons.''',
['Charge: 0.','Location: nucleus; approximate mass: 1 u.','Changing neutrons changes the isotope, not the element.'],
'Hydrogen-1 has 1 proton and 0 neutrons. Hydrogen-2 has 1 proton and 1 neutron. Both are hydrogen.',
'Neutral means no electric charge; it does not mean the particle has no mass.',
'What changes when carbon-12 becomes carbon-13?',['Proton number','Neutron number','Element name'],1,'Both have six protons; carbon-13 has one more neutron.'),
lesson('electron','Electrons','Tiny negative particles with a big chemical role.',
'''An **electron** has relative charge **−1**. Its mass is about 1/1836 of a proton’s mass, so school calculations of mass number do not count electrons.

Electrons occupy the region outside the nucleus. They are involved in bonding, electric charge and many chemical changes. A **neutral atom** has equal numbers of protons and electrons, so the positive and negative charges balance.

If an atom loses electrons, it becomes a positive ion. If it gains electrons, it becomes a negative ion. The protons are unchanged, so the element remains the same.''',
['Charge: −1.','Electrons are outside the nucleus and much lighter than protons.','A neutral atom has equal proton and electron numbers.'],
'A neutral sodium atom has 11 protons and 11 electrons. Losing one electron produces Na⁺ with 10 electrons.',
'Positive ions form by losing negative electrons, not by gaining protons.',
'A particle has 6 protons and 7 electrons. Its net charge is…',['+1','0','−1'],2,'Six positive charges plus seven negative charges leave one net negative charge.'),
lesson('atomic_number','Atomic number','Z tells you which element you have.',
'''The **atomic number**, written Z, equals the number of protons in a nucleus. The periodic table orders elements by this number.

For a neutral atom, electron number also equals Z. This second equality is not true for a charged ion. For example, both Na and Na⁺ have Z = 11, but they have 11 and 10 electrons respectively.

In nuclear notation, the atomic number appears at the lower left of the element symbol. Knowing Z lets you identify the element even when the neutron number or electron number changes.''',
['Z = number of protons.','For neutral atoms only, electrons = Z.','Isotopes and ions of an element keep the same Z.'],
'If Z = 8, the element is oxygen. Neutral oxygen has 8 electrons; O²⁻ has 10 electrons but still Z = 8.',
'Atomic number is not the sum of protons and neutrons.',
'Na⁺ contains 11 protons and 10 electrons. What is Z?',['10','11','21'],1,'Z counts protons, so it remains 11.'),
lesson('mass_number','Mass number','Count the particles in the nucleus.',
'''The **mass number**, A, is the total number of **protons plus neutrons** in one nucleus. These two kinds of particle are collectively called nucleons.

Use **A = Z + N**, where N is the neutron number. Rearranging gives **N = A − Z**. Because it counts particles, mass number is a whole number and has no unit.

Do not confuse mass number with relative atomic mass on a periodic table. Relative atomic mass can be a decimal because it reflects isotopic masses and their abundances. Mass number names a particular isotope, such as carbon-12.''',
['A = protons + neutrons.','Neutrons = A − Z.','Electrons are not included in mass number.'],
'Sodium-23 has Z = 11. Its neutron count is 23 − 11 = 12. Losing an electron does not change A.',
'Mass number is not the same as a decimal atomic mass printed on a periodic table.',
'An atom has 8 protons and 10 neutrons. What is A?',['8','10','18'],2,'Add the nucleons: 8 + 10 = 18.'),
lesson('counting','Counting particles','Read the symbol, then work step by step.',
'''Nuclear notation places **A at the upper left** and **Z at the lower left** of an element symbol. An ion’s charge is written at the upper right.

1. Read Z to find the number of **protons**.
2. Subtract Z from A to find **neutrons**.
3. For a neutral atom, **electrons = Z**.
4. For a positive ion, subtract the positive charge from Z. For a negative ion, add the magnitude of the negative charge.

These are counting rules, not instructions for physically changing a nucleus. Always check whether the question says atom or ion before deciding the electron count.''',
['Protons = Z.','Neutrons = A − Z.','Electrons = Z − signed charge.'],
'For ²³₁₁Na⁺: protons = 11; neutrons = 23 − 11 = 12; electrons = 11 − 1 = 10.',
'A superscript + refers to electric charge, not one extra neutron.',
'For ¹⁶₈O²⁻, how many electrons are present?',['6','8','10'],2,'A 2− charge means two extra electrons: 8 + 2 = 10.'),
lesson('isotopes','Isotopes','Same element. Different neutron count.',
'''**Isotopes** are atoms of the same element with the same atomic number but different mass numbers. Their proton counts match; their neutron counts differ.

Carbon-12 has 6 protons and 6 neutrons. Carbon-13 has 6 protons and 7 neutrons. Neutral atoms of both isotopes have 6 electrons, so their chemical behaviour is generally similar, though some physical properties differ.

Some isotopes are stable, while others are radioactive. Carbon-14 is radioactive and is used in radiocarbon dating of suitable once-living materials. Not every isotope is radioactive. Our explorer can count particles but does not predict nuclear stability or decay.''',
['Same Z, different A.','Neutron numbers differ.','Some isotopes are stable; some are radioactive.'],
'Carbon-12 and carbon-14 are both carbon: 6 protons each. Their neutron counts are 6 and 8.',
'Isotopes do not differ in proton number.',
'Which pair contains isotopes?',['Carbon-12 and carbon-14','Carbon-14 and nitrogen-14','Hydrogen and helium'],0,'The carbon pair has the same proton count but different neutron counts.'),
lesson('isobars','Isobars','Equal mass numbers across different elements.',
'''**Isobars** are atoms of different elements with the same mass number. They have different atomic numbers, so their proton counts differ.

Carbon-14 has 6 protons and 8 neutrons. Nitrogen-14 has 7 protons and 7 neutrons. Both have A = 14, making them isobars. They are not isotopes of one another because they are different elements.

Equal mass number means the same total number of nucleons. It does not mean exactly equal measured atomic mass or the same chemical properties. To distinguish isotopes from isobars, compare Z first, then A.''',
['Same A, different Z.','Isobars belong to different elements.','Equal nucleon totals do not mean identical properties.'],
'For carbon-14: 6 + 8 = 14. For nitrogen-14: 7 + 7 = 14. Same A, different Z.',
'Isobars have the same mass number, not the same proton number.',
'Carbon-14 and nitrogen-14 are…',['Isotopes','Isobars','The same element'],1,'Both have A = 14, but their atomic numbers are 6 and 7.'),
lesson('shells','Electron shells and valency','Connect electron arrangement to combining capacity.',
'''School shell models group electrons into energy levels called K, L, M and N. For the first 20 neutral elements, familiar examples include carbon **2,4**, sodium **2,8,1** and calcium **2,8,8,2**.

The outermost occupied shell contains **valence electrons**. **Valency** describes combining capacity. In simple main-group examples, atoms lose, gain or share electrons to reach a filled outer shell: a duet for the first shell or an octet in many common cases.

Sodium has one outer electron and commonly forms Na⁺, so its valency is 1. Oxygen has six outer electrons and commonly forms two bonds or O²⁻, so its valency is 2. These are useful school patterns, not universal rules for every element or ion.''',
['Shell diagrams organise electrons by energy level.','Valence electrons are in the outermost occupied shell.','Valency and valence-electron count are different ideas.'],
'Carbon has arrangement 2,4: four valence electrons and a usual valency of 4. Oxygen is 2,6 but has usual valency 2.',
'The M shell can hold more than eight electrons in general; 2,8,8,2 is a restricted first-20-elements teaching pattern.',
'Oxygen has six valence electrons. Its usual valency is…',['2','6','8'],0,'In common school examples oxygen needs two more electrons for an octet or shares in two bonds.'),
lesson('ions','Ions','An electron change produces a charged particle.',
'''An **ion** is an atom or group of atoms with a net electric charge. Here we focus on single-atom ions.

A **cation** is positive: it has fewer electrons than protons. An **anion** is negative: it has more electrons than protons. Calculate signed charge using **protons − electrons**.

Neutral sodium has 11 protons and 11 electrons. Na⁺ has 11 protons and 10 electrons. Neutral chlorine has 17 protons and 17 electrons; Cl⁻ has 18 electrons. Solid sodium chloride already contains Na⁺ and Cl⁻ held in an ionic lattice. Dissolving it in water separates these existing ions; it does not create them by transferring electrons. Ion formation leaves proton number and mass number unchanged.''',
['Lose electrons → positive ion.','Gain electrons → negative ion.','An electron change does not change the element.'],
'Cl⁻: 17 protons − 18 electrons = −1. The nucleus still identifies chlorine.',
'A negative ion has gained electrons, not gained neutrons.',
'What happens when a neutral atom loses one electron?',['It becomes a +1 ion','It becomes a −1 ion','It becomes a new element'],0,'It now has one more proton than electron, so its charge is +1.'),
lesson('revision','Practice and revision','Bring the three particles together.',
'''Start every particle-count question with three relationships: **Z = p**, **A = p + n**, and **charge = p − e**. Use them together instead of memorising isolated answers.

For magnesium-24 with charge 2+, Z = 12. Therefore p = 12, n = 24 − 12 = 12 and e = 12 − 2 = 10. The electron arrangement is 2,8 for this ion.

Compare a change one particle type at a time. A proton change means a different element. A neutron change means a different isotope of the same element. An electron change means a different charge state. In the next page, test these ideas with the 3D explorer and ask the tutor to explain your results.''',
['Element identity follows protons.','Isotope identity also depends on neutrons.','Electric charge depends on the proton–electron balance.'],
'Compare ¹²₆C, ¹³₆C and ¹²₆C⁻: the second changes neutrons; the third changes electrons. All have six protons.',
'Changing one particle type does not automatically change all the other counts.',
'Mg²⁺ with Z = 12 and A = 24 contains…',['12 p, 12 n, 10 e','10 p, 14 n, 12 e','12 p, 24 n, 14 e'],0,'p = 12; n = 24 − 12 = 12; e = 12 − 2 = 10.')
]
BY_ID = {l['id']: l for l in LESSONS}
PARTS = {
 'proton':('Proton','proton','Positive (+1), about 1 u, inside the nucleus. Proton count identifies the element.'),
 'neutron':('Neutron','neutron','Uncharged, about 1 u, inside the nucleus. Neutron count distinguishes isotopes.'),
 'electron':('Electron','electron','Negative (−1), much lighter than a proton, outside the nucleus. Electron count affects charge.'),
 'nucleus':('Nucleus','structure','The central region containing protons and usually neutrons; it contains almost all atomic mass.'),
 'shell':('Electron shell','shells','A simplified representation of an electron energy level, not a physical circular track.')
}
