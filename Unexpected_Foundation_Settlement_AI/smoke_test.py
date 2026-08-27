"""Run every Streamlit route. Usage: python smoke_test.py"""
import sys
from streamlit.testing.v1 import AppTest
import bridge

def run(stage):
    at=AppTest.from_file("app.py",default_timeout=180)
    at.query_params["stage"]=stage
    at.run()
    if at.exception:
        for error in at.exception:
            print(f"FAIL ?stage={stage}\n{error.message}")
        return False
    print(f"ok   ?stage={stage}")
    return True

if __name__=="__main__":
    ok=all(run(s) for s in ["start"]+bridge.ORDER)
    print("ALL PAGES OK" if ok else "FAILURES ABOVE")
    sys.exit(0 if ok else 1)
