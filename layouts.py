from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout

Builder.load_file('arm1eng1.kv')
Builder.load_file('arm1eng2.kv')
Builder.load_file('arm2eng1.kv')
Builder.load_file('arm2eng2.kv')

class Arm1Eng1(FloatLayout):
    pass

class Arm1Eng2(FloatLayout):
    pass

class Arm2Eng1(FloatLayout):
    pass

class Arm2Eng2(FloatLayout):
    def changeElement(self, state, refer):
        if(state == 'normal'):
            refer.pos_hint = {'top': 2}
        else:
            refer.pos_hint = {'top':.8}
