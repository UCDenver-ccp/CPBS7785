class MOPsManager:
    type_mop = "mop"
    type_instance = "instance"

    def __init__(self):
        self.frames = {}

    '''
    ADDERS
    '''

    def add_frame(self, name, frame_type, abstractions, slots, _id=None):
        if _id in self.frames:
            new_frame = self.frames[_id]
        elif name in self.frames:
            new_frame = self.frames[name]
        else:
            if frame_type == self.type_instance:
                new_frame = Instance(name)
            else:
                new_frame = MOP(name)

            self.frames[_id] = new_frame
            self.frames[name] = new_frame

        if abstractions is not None:
            if name in abstractions:
                abstractions.remove(name)
            self.update_abstractions(name, abstractions)
            [new_frame.add_abstraction(abstraction) for abstraction in abstractions]

        if slots is not None:
            [new_frame.add_slot(role, filler, None) for role, filler in slots.items()]

        # print("Added %s" % new_frame)
        return new_frame

    def add_mop(self, name, abstractions=None, slots=None, _id=None):
        return self.add_frame(name, frame_type=self.type_mop, abstractions=abstractions, slots=slots, _id=_id)

    def add_instance(self, name, abstractions=None, slots=None, _id=None):
        return self.add_frame(name, frame_type=self.type_instance, abstractions=abstractions, slots=slots, _id=_id)

    '''
    CHECKERS
    '''

    def is_mop(self, name):
        frame = self.frames[name]
        return frame is not None and frame.frame_type == self.type_mop

    def is_instance(self, name):
        frame = self.frames[name]
        return frame is not None and frame.frame_type == self.type_instance

    def has_slot(self, instance, role, filler):
        self.is_abstraction(filler, self.inherit_filler(instance, role))

    def has_slots(self, instance, slots):
        for role, filler in slots.items():
            if not self.has_slot(instance, role, filler):
                return False
        return True

    '''
    INHERITANCE
    '''

    def inherit(self, name, fn):
        for abstraction in self.get_all_abstractions(name):
            if fn(abstraction) is not None:
                return abstraction

    def inherit_filler(self, name, role):
        self.inherit(name, lambda abstraction: self.frames[abstraction].slots[role])

    def get_all_abstractions(self, name):
        if name not in self.frames:
            return None
        if not self.frames[name].abstractions:
            return self.frames[name].abstractions

        all_abstractions = []
        for abstraction in self.frames[name].abstractions:
            all_abstraction_abstractions = self.get_all_abstractions(abstraction)
            if all_abstraction_abstractions:
                for a in self.get_all_abstractions(abstraction):
                    all_abstractions.append(a)
        return all_abstractions

    def unlink_parent(self, specialization, abstraction):
        spec_frame = self.frames[specialization]
        if spec_frame is not None:
            spec_frame.abstractions.remove(abstraction)

    def unlink_child(self, specialization, abstraction):
        abstraction_frame = self.frames[abstraction]
        if abstraction_frame is not None:
            abstraction_frame.specs.remove(specialization)

    def unlink_abstraction(self, specialization, abstraction):
        self.unlink_parent(specialization, abstraction)
        self.unlink_child(specialization, abstraction)

    def unlink_old_abstractions(self, name, old_abstractions, new_abstractions):
        for old_abstraction in old_abstractions:
            if old_abstraction not in new_abstractions:
                self.unlink_abstraction(name, old_abstraction)

    def link_parent(self, specialization, abstraction):
        self.frames[specialization].abstractions.add(abstraction)

    def link_child(self, specialization, abstraction):
        if abstraction in self.frames:
            self.frames[abstraction].specializations.add(specialization)

    def link_abstraction(self, specialization, abstraction):
        if self.is_abstraction(abstraction, specialization):
            return
        try:
            if self.is_abstraction(specialization, abstraction):
                raise AbstractionException(specialization, abstraction)
        except AbstractionException as err:
            print(err)
            return

        self.link_parent(specialization, abstraction)
        self.link_child(specialization, abstraction)

    def link_new_abstractions(self, name, old_abstractions, new_abstractions):
        for new_abstraction in new_abstractions:
            if new_abstraction not in old_abstractions:
                if name == new_abstraction:
                    raise AbstractionException(name, new_abstraction)
                else:
                    self.link_abstraction(name, new_abstraction)

    def update_abstractions(self, name, abstractions):
        old_abstractions = self.frames[name].abstractions
        new_abstractions = set(abstractions)

        if old_abstractions != new_abstractions:
            self.unlink_old_abstractions(name, old_abstractions, new_abstractions)
            self.link_new_abstractions(name, old_abstractions, new_abstractions)

    '''
    GETTERS
    '''

    def get_instances(self, abstraction, slots):
        if self.is_instance(abstraction) and self.has_slots(abstraction, slots):
            return list(abstraction)
        else:
            return [instance for specialization in self.frames[abstraction].specs
                    for instance in self.get_instances(specialization, slots)]

    def get_root_frames(self):
        roots = []
        [roots.append(key) for key, value in self.frames.items() if value.abstractions is not None]
        return roots

    '''
    REMOVERS
    '''

    def clear_frames(self):
        self.frames.clear()

    def is_strict_abstraction(self, specialization, abstraction):
        return abstraction is not specialization and self.is_abstraction(abstraction, specialization)

    def is_abstraction(self, abstraction, specialization):
        if abstraction is specialization:
            return True
        specialization_abstractions = self.get_all_abstractions(specialization)
        if specialization_abstractions is not None:
            for spec_abstraction in specialization_abstractions:
                if abstraction is spec_abstraction:
                    return True

        return False

    def is_redundant_abstraction(self, name, abstractions):
        if self.frames[name].specs is None:
            return False
        for abstraction in abstractions:
            if not self.is_strict_abstraction(name, abstraction):
                return False

        return True

    def get_frame(self, node):
        return self.frames.get(node)

    def show_frame(self, name_or_frame, max_depth=2):
        self.pretty_print_frame_info(name_or_frame, 0, max_depth)

    def pretty_print_frame_info(self, x, depth, max_depth):
        frame = x if isinstance(x, Frame) else self.frames.get(x)
        if frame and depth != max_depth:
            self.pretty_print_frame_name(frame, depth)
            self.pretty_print_frame_type(frame, depth)
            self.pretty_print_frame_abstractions(frame, depth, max_depth)
            if isinstance(frame, MOP):
                self.pretty_print_frame_slots(frame, depth, max_depth)

    @staticmethod
    def pretty_print_frame_name(frame, depth):
        print("\t" * depth + "NAME %s" % frame.name)

    @staticmethod
    def pretty_print_frame_type(frame, depth):
        print("\t" * depth + "TYPE %s" % type(frame))

    def pretty_print_frame_abstractions(self, frame, depth, max_depth):
        for abstraction in frame.abstractions:
            name = abstraction.name if isinstance(abstraction, Frame) else abstraction
            print("\t" * depth + "ISA %s" % name)
            self.pretty_print_frame_info(abstraction, depth + 1, max_depth)

    def pretty_print_frame_slots(self, mop, depth, max_depth):
        for slot in mop.slots.values():
            print("\t" * depth + "ROLE %s" % slot.role)
            if isinstance(slot.filler, Frame):
                self.pretty_print_frame_info(slot.filler, depth + 1, max_depth)
            else:
                print("\t" * depth + "FILLER %s" % slot.filler)


class AbstractionException(Exception):
    def __init__(self, specialization, abstraction):
        self.message = '%s can\'t be an abstraction of %s' % (specialization, abstraction)


class Slot:
    role = ""
    filler = ""
    constraint = ""

    def __init__(self, role, filler, constraint):
        self.constraint = constraint
        self.filler = filler
        self.role = role


class Frame:

    def __init__(self, name):
        self.name = name
        self.abstractions = set()
        self.slots = {}

    def add_abstraction(self, abstraction):
        self.abstractions.add(abstraction)

    def add_slot(self, role, filler, constraint):
        self.slots[role] = Slot(role, filler, constraint)

    def __str__(self):
        return "frame -> name: %s abstractions: %s" % (self.name, self.abstractions)


class MOP(Frame):

    def __init__(self, name):
        super().__init__(name)
        self.specializations = set()

    def add_specialization(self, specialization):
        self.specializations.add(specialization)


class Instance(Frame):

    def __init__(self, name):
        super().__init__(name)
