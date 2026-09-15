"""Original teaching notes aligned to NCERT Class 10 Life Processes."""
SOURCE='https://www.ncert.nic.in/textbook/pdf/jesc105.pdf'
DATA=[
('pump','The heart: a living pump','A small organ with a continuous job',
'''Cells need oxygen and nutrients, and their wastes must be carried away. Blood transports these materials. The heart is a muscular organ, roughly the size of your fist, between the lungs and slightly towards the left. Its contractions keep blood moving through vessels.

Think of the heart as two coordinated pumps. The right side sends blood to the lungs; the left side sends blood to the body. The heart moves blood—it does not add oxygen. Oxygen enters the blood in the lungs.''',
['Blood transports; the heart pumps.','The two sides serve different circuits.','Both sides work together.'],
'When you climb stairs, your working muscles need more oxygen. Circulation can deliver more blood to support this demand.',
'The heart does not make oxygen.', 'Where does blood gain oxygen?', ['Lungs','Right ventricle','Aorta'],0,'Oxygen moves from air in the lungs into the blood.'),
('chambers','Four chambers','Two receiving rooms. Two pumping rooms.',
'''The upper chambers, the right and left atria, receive blood. The lower chambers, the right and left ventricles, pump blood out.

The right atrium receives oxygen-poor blood from the body and passes it into the right ventricle. The left atrium receives oxygen-rich blood from the lungs and passes it into the left ventricle. Right and left refer to the person’s body. In a front view, the right side of the heart appears on your left.''',
['Right atrium → right ventricle → lungs.','Left atrium → left ventricle → body.','Atria receive; ventricles pump out.'],
'Trace a drop returning from your leg: it enters the right atrium before the right ventricle.',
'The left atrium does not pump directly into the aorta.', 'Which chamber pumps blood towards the body?', ['Right atrium','Left ventricle','Left atrium'],1,'The left ventricle ejects blood into the aorta.'),
('septum','Keeping the two sides separate','A wall that prevents mixing',
'''The septum is the separating wall between the right and left sides of the heart. In a normal heart, blood does not cross this wall. Oxygen-rich and oxygen-poor blood remain separate inside the heart.

This separation supports efficient oxygen delivery. Birds and mammals have high energy requirements, including the energy used to maintain body temperature. Blood goes from the right side to the left side through the lungs, not through the septum.''',
['The septum is a wall, not a valve.','Right side → lungs → left side.','Separation supports efficient oxygen delivery.'],
'Find the central wall in the cutaway: no flow arrow goes through it.',
'Deoxygenated blood is relatively oxygen-poor; it is not completely without oxygen.', 'What is the main purpose of the septum?', ['Add oxygen','Prevent mixing between sides','Pump to lungs'],1,'The septum separates the right and left chambers.'),
('vessels','The major blood vessels','Learn the entrances and exits',
'''The venae cavae return blood from the body to the right atrium. The superior vena cava mainly drains the upper body; the inferior vena cava mainly drains the lower body. The pulmonary artery carries blood from the right ventricle towards the lungs.

Pulmonary veins return oxygen-rich blood from the lungs to the left atrium. The aorta carries blood from the left ventricle to the body. An artery carries blood away from the heart, regardless of oxygen content.''',
['Vena cava: body → right atrium.','Pulmonary artery: right ventricle → lungs.','Pulmonary veins: lungs → left atrium; aorta: left ventricle → body.'],
'At the lungs, blood arrives through pulmonary arteries and returns to the heart through pulmonary veins.',
'Not every artery carries oxygen-rich blood.', 'Which vessels return oxygen-rich blood to the heart?', ['Vena cava','Pulmonary artery','Pulmonary veins'],2,'Pulmonary veins enter the left atrium.'),
('valves','Valves: one-way doors','Keeping blood moving forward',
'''Valves respond to pressure differences: they open for forward flow and close to prevent backflow. Valves between atria and ventricles prevent blood returning to the atria during ventricular contraction. Outlet valves prevent blood returning from arteries during ventricular relaxation.

Focus on the one-way function for Class 10. Optional names: tricuspid between the right atrium and ventricle; mitral (bicuspid) between the left atrium and ventricle; pulmonary at the right ventricular exit; aortic at the left ventricular exit.''',
['Valves respond to pressure.','Valves prevent backflow; muscle pumps.','The model uses simplified valve flaps.'],
'During ventricular contraction, inlet valves close so blood is directed towards the arteries.',
'All four valves do not stay open together.', 'What does a valve prevent?', ['Backward flow','Oxygen entering blood','Muscle contraction'],0,'Valves maintain one-way blood flow.'),
('walls','Muscular walls','Structure suits the pumping job',
'''Ventricles have thicker muscular walls than atria because they pump blood out of the heart. Atria move blood into nearby ventricles.

The left ventricle has a particularly thick wall to generate higher pressure for body circulation. The right ventricle supplies the lower-pressure lung circulation. Normally, the two sides move the same volume over time: higher pressure does not mean one side continually pumps more blood than the other.''',
['Ventricular walls are thicker than atrial walls.','The left ventricle generates higher pressure.','Wall thickness is different from chamber size.'],
'Compare the visible wall rims of the two ventricles in the cutaway.',
'The left ventricle is not thicker because its blood contains more oxygen.', 'Why is the left ventricular wall especially thick?', ['To store food','To generate pressure for body circulation','To receive blood first'],1,'Its muscle generates pressure for systemic circulation.'),
('beat','How a heartbeat works','Fill, contract, eject, relax',
'''During relaxation, blood enters the atria and flows into relaxed ventricles. Atrial contraction helps finish ventricular filling. Next, both ventricles contract: inlet valves close and pressure eventually opens the outlet valves, sending blood into the pulmonary artery and aorta.

The ventricles relax and the cycle repeats. Contraction is called systole; relaxation is called diastole. These terms can describe a particular chamber. Both ventricles contract together—not one after the other.''',
['Atrial contraction precedes ventricular contraction.','Both ventricles pump together.','Pause freezes a teaching animation, not a medical condition.'],
'Pause during ventricular contraction and find the two outgoing vessels.',
'A blood cell does not complete an entire body circuit in one beat.', 'Which chambers pump out at the same time?', ['Both ventricles','Only the right chambers','Left atrium and right ventricle'],0,'The ventricles send blood into the two circuits together.'),
('pathway','Follow a drop of blood','One route, learned step by step',
'''Blood returning from body tissues enters a vena cava, the right atrium and then the right ventricle. It leaves through the pulmonary artery. In the lungs, it releases carbon dioxide and gains oxygen.

Blood returns through pulmonary veins to the left atrium, enters the left ventricle and leaves through the aorta. Body capillaries deliver oxygen to tissues and collect carbon dioxide. Veins carry blood back towards the heart.''',
['Body → vena cava → right atrium → right ventricle.','Pulmonary artery → lungs → pulmonary veins.','Left atrium → left ventricle → aorta → body.'],
'Trace the numbered diagram with your finger, then locate each heart structure in 3D.',
'Blood does not move directly from the right ventricle into the left ventricle.', 'What follows the right ventricle?', ['Aorta','Pulmonary artery','Left atrium'],1,'Blood exits into the pulmonary artery.'),
('double','Double circulation','Two circuits, one complete journey',
'''Pulmonary circulation connects the right ventricle, lungs and left atrium. Systemic circulation connects the left ventricle, body tissues and right atrium.

Together they form double circulation: blood passes through the heart twice during a complete lung-and-body circuit. Separation helps efficient oxygen delivery. Compare fish: their two-chambered heart pumps through a single circuit—heart → gills → body → heart.''',
['Pulmonary: the lung circuit.','Systemic: the body circuit.','Twice counts heart passages, not heartbeats.'],
'Draw two loops that share the heart: one reaches the lungs; one reaches the body.',
'Double circulation does not mean two separate hearts.', 'Why is circulation called double?', ['Two aortas','Two passages through the heart per complete circuit','Only two heartbeats'],1,'Each circuit involves a passage through the heart.'),
('types','Arteries, veins and capillaries','Three designs for three jobs',
'''Arteries carry blood away from the heart. Their thick, elastic walls withstand the pressure of blood leaving the heart. Veins return blood towards the heart at lower pressure; many veins have valves to prevent backflow.

Capillaries have walls only one cell thick. Materials exchange between the blood and tissues across these thin walls. Arteries branch into smaller vessels and capillaries; capillaries connect with vessels that join into veins. Use direction, not oxygen content, to distinguish arteries from veins.''',
['Arteries: away.','Veins: towards.','Capillaries: exchange.'],
'In a muscle, oxygen moves from capillary blood towards cells; carbon dioxide moves towards the blood.',
'A vein is not defined as a vessel carrying oxygen-poor blood.', 'What helps capillaries exchange materials?', ['One-cell-thick walls','Very thick muscle','Large valves'],0,'A thin wall gives materials a short exchange path.'),
]
KEYS=['id','title','subtitle','text','points','example','misconception','question','options','answer','why']
LESSONS=[dict(zip(KEYS,row)) for row in DATA]
BY_ID={l['id']:l for l in LESSONS}
PARTS={
'right_atrium':('Right atrium','chambers','Receives oxygen-poor blood returning from the body.'),
'left_atrium':('Left atrium','chambers','Receives oxygen-rich blood returning from the lungs.'),
'right_ventricle':('Right ventricle','walls','Pumps blood through the pulmonary artery towards the lungs.'),
'left_ventricle':('Left ventricle','walls','Pumps blood into the aorta for the body.'),
'septum':('Septum','septum','Separates the right and left sides of the heart.'),
'vena_cava':('Venae cavae','vessels','Return blood from the upper and lower body to the right atrium.'),
'pulmonary_artery':('Pulmonary artery','vessels','Carries oxygen-poor blood from the right ventricle to the lungs.'),
'pulmonary_veins':('Pulmonary veins','vessels','Return oxygen-rich blood from the lungs to the left atrium.'),
'aorta':('Aorta','vessels','Carries oxygen-rich blood from the left ventricle to the body.'),
'tricuspid':('Tricuspid valve','valves','Prevents backflow from the right ventricle into the right atrium.'),
'mitral':('Mitral valve','valves','Prevents backflow from the left ventricle into the left atrium.'),
'pulmonary_valve':('Pulmonary valve','valves','Prevents backflow from the pulmonary artery into the right ventricle.'),
'aortic_valve':('Aortic valve','valves','Prevents backflow from the aorta into the left ventricle.'),
}
