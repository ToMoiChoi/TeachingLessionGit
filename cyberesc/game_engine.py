class GameEngine:
    def __init__(self, screen):
        # Tránh lỗi Circular Import bằng cách import trực tiếp trong __init__
        from game_engine_gameplay import GameplayManager
        from game_engine_layout import LayoutRenderer

        self.gameplay = GameplayManager(screen)
        self.layout = LayoutRenderer(screen)

    @property
    def state(self):
        return self.gameplay.state

    @state.setter
    def state(self, value):
        self.gameplay.state = value

    def handle_event(self, event):
        self.gameplay.handle_event(event)

    def update_game_logic(self):
        self.gameplay.update_game_logic()

    def render(self):
        self.layout.render(self.gameplay)

    def update_and_render(self):
        self.gameplay.update_game_logic()
        self.layout.render(self.gameplay)

    def __getattr__(self, name):
        """
        Tự động chuyển tiếp (delegate) mọi truy cập thuộc tính hoặc phương thức 
        chưa có ở GameEngine sang object `gameplay`.
        Giúp menu.py, main.py hay các file khác vẫn gọi trực tiếp engine.coins,
        engine.player, engine.start_level(),... mà không bị lỗi.
        """
        return getattr(self.gameplay, name)