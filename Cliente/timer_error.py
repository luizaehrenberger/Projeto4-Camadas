# Erro para quando o tempo de espera por uma mensagem é maior do que 5 segundos
class Timer1Error(Exception):
    def __init__(self, message='Cliente demorou mais que o esperado no timer 1')->None:
        self.message = message
        super().__init__(self.message)

# Erro para quando o tempo de espera por uma mensagem é maior do que 20 segundos
class Timer2Error(Exception):
    def __init__(self, message='Cliente demorou mais que o esperado no timer 2')->None:
        self.message = message
        super().__init__(self.message) 