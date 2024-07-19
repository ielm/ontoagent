from ontoagent.agent import Agent
from ontoagent.engine.executable import ProactiveExecutable


class UpdateEvergreenGoalsProactiveExecutable(ProactiveExecutable):

    def run(self, agent: Agent):
        agent.evergreens().update()
        current_goals = agent.agenda().goals()
        for resolution in agent.evergreens().pending_resolutions():
            if resolution not in current_goals:
                agent.agenda().add_goal(resolution)
