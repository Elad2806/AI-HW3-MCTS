import itertools

from Simulator import Simulator
import math
import random
from copy import deepcopy


IDS = ["Your IDS here"]

class Agent:
    def __init__(self, initial_state, player_number):
        init_copy = deepcopy(initial_state)
        self.ids = IDS
        self.player_number = player_number
        self.rival_number = 2 if player_number == 1 else 1
        Node.player_number = self.player_number
        Node.rival_number = self.rival_number
        self.my_taxis = []
        self.rival_taxis = []
        self.simulator = Simulator(init_copy)
        self.moves_history = []
        for taxi_name, taxi in init_copy['taxis'].items():
            if taxi['player'] == player_number:
                self.my_taxis.append(taxi_name)
            else:
                self.rival_taxis.append(taxi_name)

    def selection(self, UCT_tree):
        current_node = UCT_tree.root_node
        while len(current_node.children) != 0:
            current_node = current_node.select_child()
        return current_node


    def expansion(self, UCT_tree, parent_node):
        """
        this method generates the children of a selected node
        """
        curr_player = self.get_curr_player(parent_node)
        #print(parent_node.representing_simulator_state)
        #print(curr_player,self.player_number)
        parent_node.node_simulator.set_state(deepcopy(parent_node.representing_simulator_state))
        actions = self.get_moves(parent_node.representing_simulator_state)
        for action in actions:

           # print(parent_node.representing_simulator_state)
            parent_node.node_simulator.apply_action(action, curr_player)

            #print(parent_node.representing_simulator_state)
            parent_node.add_child(action,parent_node.node_simulator.get_state(),parent_node.node_simulator.get_score())
            parent_node.node_simulator.set_state(deepcopy(parent_node.representing_simulator_state))
            parent_node.node_simulator.score = deepcopy(parent_node.initial_score)
            parent_node.node_simulator.get_state()['turns to go'] += 1

        #print("999999999999999999999999999999999999999999999999999")



    def simulation(self,UCT_tree,node, curr_player = None, flag = None):
        other_player = 1 if curr_player == 2 else 2
        if flag:
            node.node_simulator.set_state(deepcopy(node.representing_simulator_state))
            node.node_simulator.get_state()['turns to go'] = node.turns_to_go

        curr_state = node.node_simulator.get_state()
        #print(curr_player)
        #print(node.node_simulator.get_state()['turns to go'])
        if node.node_simulator.get_state()['turns to go'] == 0:
            return node.node_simulator.get_score()
        actions = self.get_moves(curr_state)
        action = self.choose_action(curr_player,actions,curr_state)
        action = random.choice(actions)
        node.node_simulator.apply_action(action, curr_player)
        child_representing_state = node.node_simulator.get_state()
        #print(child_representing_state)


        return self.simulation(UCT_tree,node,other_player,0)

    def choose_action(self,curr_player,actions,curr_state):
        curr_taxis = self.my_taxis if curr_player == self.player_number else self.rival_taxis
        for action in actions:
            action_value = 0
            simulator = Simulator(deepcopy(curr_state))
            simulator.apply_action(action, curr_player)
            action_value += 10 * simulator.score.get(f'player {curr_player}')
            new_state = simulator.get_state()

            for taxi in curr_taxis:
                # adding reward or penalty based on the difference between the old and new state distance from goal
                taxi_passengers = set()
                for passenger,passenger_items in new_state['passengers'].items():
                    if passenger_items['location'] == taxi:
                        taxi_passengers.add((passenger,passenger_items))
                for passenger in taxi_passengers:
                    old_state_distance = self.get_distance(curr_state['taxis'][taxi]['location'],
                                                           passenger[1]['destination'])
                    new_state_distance = self.get_distance(new_state['taxis'][taxi]['location'],passenger[1]['location'])
                    action_value += old_state_distance - new_state_distance

                for passenger,passenger_items in new_state['passengers'].items():
                    if type(passenger_items['location']) == tuple: #psngr not in taxi
                        old_state_distance = math.sqrt(self.get_distance(curr_state['taxis'][taxi]['location'],
                                                               passenger[1]['destination']))
                        new_state_distance = math.sqrt(self.get_distance(new_state['taxis'][taxi]['location'],passenger[1]['location']))
                        action_value += old_state_distance - new_state_distance




    def backpropagation(self, simulation_result,node):
        while node is not None:
            node.update(simulation_result)
            node = node.parent

    def get_moves(self, state) :
        curr_player = None
        curr_taxis = None
        if self.player_number == 1:
            if state['turns to go'] % 2 == 0:
                curr_player = self.player_number
                curr_taxis = self.my_taxis
            else:
                curr_player = self.rival_number
                curr_taxis = self.rival_taxis
        else:
            if state['turns to go'] % 2 == 0:
                curr_player = self.rival_number
                curr_taxis = self.rival_taxis
            else:
                curr_player = self.player_number
                curr_taxis = self.my_taxis

        actions = {}
        self.simulator.set_state(state)
        for taxi in curr_taxis:
            actions[taxi] = set()
            neighboring_tiles = self.simulator.neighbors(state["taxis"][taxi]["location"])
            for tile in neighboring_tiles:
                actions[taxi].add(("move", taxi, tile))
            if state["taxis"][taxi]["capacity"] > 0:
                for passenger in state["passengers"].keys():
                    if state["passengers"][passenger]["location"] == state["taxis"][taxi]["location"]:
                        actions[taxi].add(("pick up", taxi, passenger))
            for passenger in state["passengers"].keys():
                if (state["passengers"][passenger]["destination"] == state["taxis"][taxi]["location"]
                        and state["passengers"][passenger]["location"] == taxi):
                    actions[taxi].add(("drop off", taxi, passenger))
            actions[taxi].add(("wait", taxi))

        actions_list = []
        for taxi,actions in actions.items():
            actions_list.append(list(actions))

        all_actions = list(itertools.product(*actions_list))
        all_legal_actions = []
        for action in all_actions:

            is_legal = self.simulator.check_if_action_legal(action, curr_player)
            if is_legal:
                all_legal_actions.append(action)

        return all_legal_actions


    def act(self, state):
        state_copy = deepcopy(state)
        #print(state)
        UCT_Tree = Tree(state_copy)
        #print(UCT_Tree.root_node.representing_simulator_state)
        iterations = 60
        for iteration in range(iterations):
            node = self.selection(UCT_Tree)
            if node.representing_simulator_state['turns to go'] == 0:

                self.backpropagation(node.node_simulator.get_score(),node)
            else:
                self.expansion(UCT_Tree,node)
                result = self.simulation(UCT_Tree,node,self.player_number,1)
                self.backpropagation(deepcopy(result), node)
                #print(UCT_Tree.root_node.representing_simulator_state)
                node.node_simulator.set_state(deepcopy(node.representing_simulator_state))
                node.node_simulator.score = deepcopy(node.initial_score)
                node.node_simulator.turns_to_go = node.turns_to_go
                #print(result)
        #print(UCT_Tree.root_node.representing_simulator_state)
        res = max(UCT_Tree.root_node.children, key=lambda child: child.total_score / child.visits)  # No exploration

        """
        for child in UCT_Tree.root_node.children:
            print(child.state, child.total_score, child.visits, child.total_score / child.visits)
            if "drop off" in str(child.state):
                print(child.initial_score)
                print(child.node_simulator.score)
        """""
        return res.state[0]

    def get_curr_player(self,node):
        curr_player = None

        if self.player_number == 1:
            if node.depth % 2 == 0:
                curr_player = self.player_number

            else:
                curr_player = self.rival_number

        else:
            if node.depth % 2 == 0:
                curr_player = self.player_number

            else:
                curr_player = self.rival_number
        return curr_player






class UCTAgent:
    def __init__(self, initial_state, player_number):
        init_copy = deepcopy(initial_state)
        self.ids = IDS
        self.player_number = player_number
        self.rival_number = 2 if player_number == 1 else 1
        Node.player_number = self.player_number
        Node.rival_number = self.rival_number
        self.my_taxis = []
        self.rival_taxis = []
        self.simulator = Simulator(init_copy)
        self.moves_history = []
        for taxi_name, taxi in init_copy['taxis'].items():
            if taxi['player'] == player_number:
                self.my_taxis.append(taxi_name)
            else:
                self.rival_taxis.append(taxi_name)

    def selection(self, UCT_tree):
        current_node = UCT_tree.root_node
        while len(current_node.children) != 0:
            current_node = current_node.select_child()
        return current_node


    def expansion(self, UCT_tree, parent_node):
        """
        this method generates the children of a selected node
        """
        curr_player = self.get_curr_player(parent_node)
        #print(parent_node.representing_simulator_state)
        #print(curr_player,self.player_number)
        parent_node.node_simulator.set_state(deepcopy(parent_node.representing_simulator_state))
        actions = self.get_moves(parent_node.representing_simulator_state)
        for action in actions:

           # print(parent_node.representing_simulator_state)
            parent_node.node_simulator.apply_action(action, curr_player)

            #print(parent_node.representing_simulator_state)
            parent_node.add_child(action,parent_node.node_simulator.get_state(),parent_node.node_simulator.get_score())
            parent_node.node_simulator.set_state(deepcopy(parent_node.representing_simulator_state))
            parent_node.node_simulator.score = deepcopy(parent_node.initial_score)
            parent_node.node_simulator.get_state()['turns to go'] += 1

        #print("999999999999999999999999999999999999999999999999999")



    def simulation(self,UCT_tree,node, curr_player = None, flag = None):
        other_player = 1 if curr_player == 2 else 2
        if flag:
            node.node_simulator.set_state(deepcopy(node.representing_simulator_state))
            node.node_simulator.get_state()['turns to go'] = node.turns_to_go

        curr_state = node.node_simulator.get_state()
        #print(curr_player)
        #print(node.node_simulator.get_state()['turns to go'])
        if node.node_simulator.get_state()['turns to go'] == 0:
            return node.node_simulator.get_score()
        actions = self.get_moves(curr_state)
        action = random.choice(actions)
        node.node_simulator.apply_action(action, curr_player)
        child_representing_state = node.node_simulator.get_state()
        #print(child_representing_state)


        return self.simulation(UCT_tree,node,other_player,0)



    def backpropagation(self, simulation_result,node):
        while node is not None:
            node.update(simulation_result)
            node = node.parent

    def get_moves(self, state) :
        curr_player = None
        curr_taxis = None
        if self.player_number == 1:
            if state['turns to go'] % 2 == 0:
                curr_player = self.player_number
                curr_taxis = self.my_taxis
            else:
                curr_player = self.rival_number
                curr_taxis = self.rival_taxis
        else:
            if state['turns to go'] % 2 == 0:
                curr_player = self.rival_number
                curr_taxis = self.rival_taxis
            else:
                curr_player = self.player_number
                curr_taxis = self.my_taxis

        actions = {}
        self.simulator.set_state(state)
        for taxi in curr_taxis:
            actions[taxi] = set()
            neighboring_tiles = self.simulator.neighbors(state["taxis"][taxi]["location"])
            for tile in neighboring_tiles:
                actions[taxi].add(("move", taxi, tile))
            if state["taxis"][taxi]["capacity"] > 0:
                for passenger in state["passengers"].keys():
                    if state["passengers"][passenger]["location"] == state["taxis"][taxi]["location"]:
                        actions[taxi].add(("pick up", taxi, passenger))
            for passenger in state["passengers"].keys():
                if (state["passengers"][passenger]["destination"] == state["taxis"][taxi]["location"]
                        and state["passengers"][passenger]["location"] == taxi):
                    actions[taxi].add(("drop off", taxi, passenger))
            actions[taxi].add(("wait", taxi))

        actions_list = []
        for taxi,actions in actions.items():
            actions_list.append(list(actions))

        all_actions = list(itertools.product(*actions_list))
        all_legal_actions = []
        for action in all_actions:

            is_legal = self.simulator.check_if_action_legal(action, curr_player)
            if is_legal:
                all_legal_actions.append(action)

        return all_legal_actions


    def act(self, state):
        state_copy = deepcopy(state)
        #print(state)
        UCT_Tree = Tree(state_copy)
        #print(UCT_Tree.root_node.representing_simulator_state)
        iterations = 60
        for iteration in range(iterations):
            node = self.selection(UCT_Tree)
            if node.representing_simulator_state['turns to go'] == 0:

                self.backpropagation(node.node_simulator.get_score(),node)
            else:
                self.expansion(UCT_Tree,node)
                result = self.simulation(UCT_Tree,node,self.player_number,1)
                self.backpropagation(deepcopy(result), node)
                #print(UCT_Tree.root_node.representing_simulator_state)
                node.node_simulator.set_state(deepcopy(node.representing_simulator_state))
                node.node_simulator.score = deepcopy(node.initial_score)
                node.node_simulator.turns_to_go = node.turns_to_go
                #print(result)
        #print(UCT_Tree.root_node.representing_simulator_state)
        res = max(UCT_Tree.root_node.children, key=lambda child: child.total_score / child.visits)  # No exploration

        """
        for child in UCT_Tree.root_node.children:
            print(child.state, child.total_score, child.visits, child.total_score / child.visits)
            if "drop off" in str(child.state):
                print(child.initial_score)
                print(child.node_simulator.score)
        """""
        return res.state[0]

    def get_curr_player(self,node):
        curr_player = None

        if self.player_number == 1:
            if node.depth % 2 == 0:
                curr_player = self.player_number

            else:
                curr_player = self.rival_number

        else:
            if node.depth % 2 == 0:
                curr_player = self.player_number

            else:
                curr_player = self.rival_number
        return curr_player


class Tree:

    def __init__(self,root_state):
        self.root_state = root_state
        self.root_node = Node([], None,root_state,{'player 1': 0, 'player 2': 0} )

    def update_root(self,new_root):
        self.root_state = new_root
        self.root_node = Node([],None,new_root,{'player 1': 0, 'player 2': 0})

class Node:
    player_number = 0
    rival_number = 0
    def __init__(self, state = None, parent=None, representing_simulator_state = None, initial_score = None ):
        # state of a node is a sequence of actions
        # this sequence can make a lot of different states, and 1 is chosen to represent it when we choose this node
        #print(state,parent,representing_simulator_state)
        self.state = state
        self.representing_simulator_state = deepcopy(representing_simulator_state)
        #print(state,representing_simulator_state)
        self.node_simulator = Simulator(deepcopy(representing_simulator_state))
        self.turns_to_go = self.representing_simulator_state['turns to go']
        self.node_simulator.turns_to_go = self.representing_simulator_state['turns to go']
        self.initial_score = deepcopy(initial_score)
        self.node_simulator.score = deepcopy(initial_score)
        self.parent = parent
        self.total_score = 0
        self.update(initial_score, 1)
        """
        if "drop off" in str(self.state):
            print(self.total_score,self.state)
            """
        self.visits = 0
        self.children = []
        if parent == None:
            self.depth = 0
        else:
            self.depth = self.parent.depth +1

    def add_child(self, action,representing_simulator_state,initial_score):

        child_state = [item for item in self.state] + [action]
        child = Node(child_state, self,representing_simulator_state,initial_score)

        self.children.append(child)
        return child

    def select_child(self):
        """"
        This method chooses a child (which represents an action), such that my agent picks the child with
        the highest UCT value, and the rival agent child is arbitrary chosen.
        """

        if Node.player_number ==1:
            curr_player = 1 if self.depth % 2 == 0 else 2
        else:
            curr_player = 2 if self.depth % 2 == 0 else 1

        return max(self.children, key=lambda child: child.uct_value())
        #a chilf of my agent is chosen by UCT value, rival agent child is chosen at random


    def get_curr_player(self):
        curr_player = None
        if Node.player_number == 1:
            if self.node_simulator.turns_to_go % 2 == 0:
                curr_player = Node.player_number

            else:
                curr_player = Node.rival_number

        else:
            if self.node_simulator.turns_to_go % 2 == 0:
                curr_player = Node.rival_number

            else:
                curr_player = Node.player_number
        return curr_player

    def update(self, result, is_initiating = 0):
        if self.player_number == 1:
            curr_player_key = "player 1"
        else:
            curr_player_key = "player 2"
        if not is_initiating:
            self.visits += 1
        self.total_score += result.get(curr_player_key)

    def uct_value(self) -> float:
        if self.visits == 0:
            return float('inf')
        return self.total_score / self.visits + math.sqrt(2 * math.log(self.parent.visits) / self.visits)


