class TaskPlanner:
    def __init__(self):
        pass

    def plan_steps(self, actions):
        """
        Processes the actions parsed by the intent engine and structures them into a plan.
        Injects dependencies such as checking network status if internet-reliant actions are detected.
        """
        plan = []
        internet_reliant_actions = ["open_url", "search_web", "toggle_wifi", "check_wifi"]
        
        # Check if internet access is needed
        needs_internet = False
        for act in actions:
            if act.get("action") in internet_reliant_actions:
                needs_internet = True
                break
                
        # If internet is required, check Wi-Fi/Internet status first (unless the first action is already a Wi-Fi command)
        if needs_internet and not (actions and actions[0].get("action") in ["check_wifi", "toggle_wifi"]):
            plan.append({
                "step": len(plan) + 1,
                "action": "check_wifi",
                "params": {},
                "response": "Ensuring we have internet access."
            })
            
        # Append the user actions
        for act in actions:
            plan.append({
                "step": len(plan) + 1,
                "action": act.get("action", "chat"),
                "params": act.get("params", {}),
                "response": act.get("response", "")
            })
            
        return plan
