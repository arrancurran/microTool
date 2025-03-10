import cv2

def calc_img_hist(self, img_data):
        if len(img_data.shape) == 3:
            img_data = cv2.cvtColor(img_data, cv2.COLOR_RGB2GRAY)

        hist = cv2.calcHist([img_data], [0], None, [256], [0, 256])
        self.hist_display.figure.clear()
        ax = self.hist_display.figure.add_subplot(111)
        ax.plot(hist, color='#97c1ff', linestyle='-', linewidth=0.5, marker='')
        ax.set_facecolor('#2c3036')
        ax.set_yscale('log')
        ax.set_xlim([0, 256])
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_frame_on(False)
        self.hist_display.figure.patch.set_facecolor('#25292E')
        
        self.hist_display.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

        self.hist_display.draw()