
from src.agents.super_agent import build_crew
from src.notification.notifications import push_notification

def application_init():
    result = None

    try:
        crew_super_agent = build_crew()
        crew_result_str = str(crew_super_agent.kickoff())
        
        result = push_notification(crew_result_str)
        
    except Exception as e:
        print(f"\n[Fatal Error] Application initialization failed: {str(e)}")
        exit(1)
    
    return result


if __name__ == "__main__":
    final_result = application_init()
    print(f"\n\n\n\n\n\n\n\n\n\n[Final Result] {final_result}\n\n\n\n\n\n\n\n")
