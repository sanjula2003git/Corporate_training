# AI CPR Guardian

A wall-mounted unit that coaches an **untrained bystander** through chest compressions:
camera, speaker and display, CPR pressure pad, AED, emergency-call link, and red / amber /
green lights.

## ⚠️ This is a teaching simulation

Everything in the notebook runs on **synthetic data generated in section 2**. No person,
helper or mannequin was recorded. It is not a medical device, it has not been tested on
anybody, and nothing in it may be used to guide real resuscitation. The real thing is a
regulated medical device.

## The design rule the whole build is shaped around

A camera must not be trusted to measure chest-compression depth. Pixels-to-centimetres
depends on lens, angle, distance, clothing and body size, and a 20% error there is the
difference between effective and useless CPR. So:

| Signal | Sensor |
|---|---|
| Posture — elbow angle, shoulders over hands, hand placement, has the helper stopped, is a second person present | **Camera** |
| Depth, rate, full recoil, excessive force | **Pressure / displacement pad** |
| Rhythm analysis | **AED** |
| **The shock decision** | **The AED. Never the coaching AI.** |

The notebook models only the *stand-clear state* the coach must enforce around the AED. It
contains no branch that decides whether to shock, and it must not grow one.

## What the notebook does

1. Simulates a 3½-minute rescue — two helpers, one AED pause, one honest case of fatigue
2. Turns camera keypoints into elbow angle and shoulder-over-hands alignment
3. Counts compressions with a hand-written peak finder
4. Measures depth, rate and recoil for every compression
5. Applies the feedback rules, one message at a time, ordered by cost to the patient
6. Detects declining performance and calls the rescuer switch
7. Enforces the AED stand-clear state
8. Draws the final CPR-quality timeline

## Two things worth knowing before you teach it

**The fatigue section is built around a failed first attempt, on purpose.** Watching peak
depth *misses* rescuer A tiring: as A stops releasing fully, each push starts from lower
down, so the chest still reaches roughly the right depth while every compression does less
work. Peak depth falls 0.59 cm; the actual stroke falls 1.32 cm. Fatigue is therefore
detected on `stroke_cm` (peak minus the residual lean), compared against that helper's *own*
first twenty compressions. The notebook shows both detectors side by side.

**The "you are alone" branch is not a nicety.** A unit that tells a solo helper to swap with
somebody has issued an instruction that cannot be followed, and the only thing it achieves is
telling them they are failing. `switch_plan(comp, second_person_available=False)` returns the
correct output instead: keep the beat going, do not stop.

## Files

| File | What it is |
|---|---|
| `AI_CPR_Guardian.ipynb` | The notebook, executed, with all figures embedded |
| `build_nb.py` | Builds the notebook. Run with `python -X utf8 build_nb.py` |

Only numpy, pandas and matplotlib — all pre-installed in Colab. The peak finder is written by
hand rather than imported, because seeing how compressions get counted is half the lesson.

## Sources for the guideline numbers

Depth 5–6 cm, rate 100–120 per minute, full recoil, chest compression fraction at least 60%,
swap rescuers about every 2 minutes. Real-time CPR feedback devices reporting rate, depth and
recoil are established practice and audiovisual feedback is considered reasonable for
optimising CPR performance. Computer-vision posture feedback is a newer and less settled
research area — which is exactly why it is kept off the depth measurement here.
