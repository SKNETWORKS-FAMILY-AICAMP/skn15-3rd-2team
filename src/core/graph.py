from langgraph.graph import StateGraph, END
from . import nodes
from .state import AgentState
from utils.utils import TODO_CATEGORIES, USER_INFO

class Graph:
    def __init__(self):
        workflow = StateGraph(AgentState)
        # 노드 추가
        workflow.add_node("initNode", nodes.initNode)
        workflow.add_node("managerNode", nodes.managerNode)
        workflow.add_node("elseNode", nodes.elseNode)
        workflow.add_node("gujicNode", nodes.gujicNode)
        workflow.add_node("outputNode", nodes.outputNode)

        # 자소서 서브그래프
        workflow.add_node("jasosuMainNode", nodes.jasosuMainNode)

        # 그래프 연결
        workflow.set_entry_point("initNode")  
        workflow.add_edge("initNode", "managerNode")

        # 매니저 -> 역할 배분
        workflow.add_conditional_edges("managerNode", 
                                       self.select_Node,
                                       {
                                           "elseNode": "elseNode",
                                            "gujicNode": "gujicNode",
                                            "jasosuMainNode": "jasosuMainNode",
                                            "outputNode" : "outputNode", 
                                       })

        # 역할완료 -> 매니저
        workflow.add_edge("elseNode", "managerNode")
        workflow.add_edge("gujicNode", "managerNode")
        workflow.add_edge("jasosuMainNode", "managerNode")
        workflow.add_edge("outputNode", END)
        self.app = workflow.compile()

    def select_Node(self, state : AgentState):
        if not state['todo_list']:
            return "outputNode"
        
        for task in state['todo_list']:
            if task[0]==TODO_CATEGORIES[0]:
                return "gujicNode"
            
        if state['todo_list'][0][0]==TODO_CATEGORIES[1]:
            return "jasosuMainNode"
        
        return "elseNode"
        


        

    def run(self, initial_state: dict):
        return self.app.invoke(initial_state)
    
