import pickle


class Loader(pickle.Unpickler):
    def find_class(self, module, name):
        if name == 'City':
            from City import City
            return City
        return super().find_class(module, name)
