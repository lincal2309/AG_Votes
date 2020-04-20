# -*-coding:Utf-8 -*

''' Tools for Votes app '''
import random
# from django.conf import settings

# debug = settings.DEBUG

# Generate secured password
pass_length = 10
pass_chars = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
              "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
              "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
              "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
              "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
              "&", "(", "-", "_", ")", "=", "#", "{", "[", "|", "\\", "@", "]",
              "}", "$", "%", "*", "?", "/", "!", "§", "<", ">"]

def define_password():
    result = "".join([random.choice(pass_chars) for x in range(0, pass_length)])
    # if debug:
    #     result = "titi"
    return result