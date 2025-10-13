class Player:
    def __init__(self, name, is_human, chip_stack, position):
        self.name = name
        self.is_human = is_human
        self.chip_stack = chip_stack
        self.position = position  # Table position (0 = dealer, etc.)
        self.hole_cards = []  # List of cards dealt to player

    def __repr__(self):
        return (f"Player(name={self.name!r}, is_human={self.is_human}, "
                f"chip_stack={self.chip_stack}, position={self.position}, "
                f"hole_cards={self.hole_cards})")

