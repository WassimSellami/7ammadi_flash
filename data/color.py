class Color:
    white = (255, 255, 255)
    black = (0, 0, 0)
    blue = (0, 0, 255)
    green = (0, 255, 0)

    paint_pink = (255, 114, 170)
    paint_gold = (254, 190, 80)
    paint_green = (74, 202, 79)
    paint_blue = (28, 154, 255)
    paint_palette = (
        ("Pink", paint_pink),
        ("Golden Yellow", paint_gold),
        ("Green", paint_green),
        ("Blue", paint_blue),
    )

    color_A = paint_green
    color_B = paint_pink

    @staticmethod
    def true_color(player):
        """use Color.true_color(player.name) to call this function. It returns players original color"""
        if player == 'Player_A':
            return Color.color_A
        else:
            return Color.color_B
