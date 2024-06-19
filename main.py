import cv2
import numpy as np
from collections import deque
from tkinter import Tk, Button, Label, filedialog
from PIL import Image, ImageTk

def find_start_end_points(image):
    # Setting the HSV color ranges for green and red.
    green_lower = np.array([40, 40, 40])
    green_upper = np.array([80, 255, 255])

    # We have a double range for red because of its double occurrence in the HSV color space
    red_lower1 = np.array([0, 50, 50])
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([170, 50, 50])
    red_upper2 = np.array([180, 255, 255])

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    green_mask = cv2.inRange(hsv, green_lower, green_upper)
    red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
    red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)

    green_points = cv2.findNonZero(green_mask)
    red_points = cv2.findNonZero(red_mask)

    if green_points is None or red_points is None:
        raise ValueError("Start or end point not found in the image")

    start_point = tuple(green_points[0][0])
    end_point = tuple(red_points[0][0])

    return start_point, end_point

def draw_walls(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        cv2.drawContours(image, [contour], -1, (0, 0, 0), 2)

    return image, binary

def bfs_search(image, start, end, binary):
    queue = deque([start])
    visited = set()
    parent = {}
    found = False

    height, width = binary.shape  # Downloading the dimensions of the binary image

    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]  #  up, right, down, left

    while queue:
        x, y = queue.popleft()
        if (x, y) == end:
            found = True
            break

        for direction in directions:
            next_x, next_y = x + direction[0], y + direction[1]
            if next_x >= 0 and next_x < width and next_y >= 0 and next_y < height:  # Checking image boundaries
                if (next_x, next_y) not in visited and binary[next_y, next_x] != 255:
                    queue.append((next_x, next_y))
                    visited.add((next_x, next_y))
                    parent[(next_x, next_y)] = (x, y)

    if not found:
        raise ValueError("Failed to find a valid path")

    # Backtracking to reconstruct the path
    path = []
    current = end
    while current != start:
        path.append(current)
        current = parent[current]
    path.append(start)
    path.reverse()

    return path

class MazeSolverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Maze Solver App")

        self.image_path = None
        self.image = None
        self.start_point = None
        self.end_point = None
        self.result_image = None

        # UI Elements
        self.label_info = Label(self.root, text="Select an image file")
        self.label_info.pack(pady=10)

        self.button_load_image = Button(self.root, text="Select Image", command=self.load_and_solve)
        self.button_load_image.pack(pady=5)

        self.label_image = Label(self.root)
        self.label_image.pack(padx=10, pady=10)

    def load_and_solve(self):
        self.image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.png;*.bmp")])
        if self.image_path:
            self.image = cv2.imread(self.image_path)
            self.solve_and_display()

    def solve_and_display(self):
        if self.image is None:
            self.label_info.config(text="No image loaded")
            return

        try:
            self.start_point, self.end_point = find_start_end_points(self.image)
            self.label_info.config(text=f"Start point: {self.start_point}, End point: {self.end_point}")

            image_with_walls, binary = draw_walls(self.image)

            # Drawing start and end points
            cv2.circle(image_with_walls, self.start_point, 5, (0, 255, 0), -1)
            cv2.circle(image_with_walls, self.end_point, 5, (0, 0, 255), -1)

            # Finding and drawing path using BFS algorithm
            path = bfs_search(image_with_walls, self.start_point, self.end_point, binary)

            # Drawing the path on the image
            for point in path:
                cv2.circle(image_with_walls, point, 2, (0, 0, 255), -1)

            # Scaling the image to fit the label
            image_height, image_width, _ = image_with_walls.shape
            max_display_width = 800
            scale_factor = max_display_width / image_width
            scaled_width = int(image_width * scale_factor)
            scaled_height = int(image_height * scale_factor)
            image_with_walls = cv2.resize(image_with_walls, (scaled_width, scaled_height))

            # Converting image back to RGB for displaying in tkinter
            image_with_walls_rgb = cv2.cvtColor(image_with_walls, cv2.COLOR_BGR2RGB)
            image_with_walls_pil = Image.fromarray(image_with_walls_rgb)
            image_with_walls_tk = ImageTk.PhotoImage(image_with_walls_pil)

            # Updating label with result image
            self.label_image.configure(image=image_with_walls_tk)
            self.label_image.image = image_with_walls_tk

            # Saving the result image
            result_filename = "output.png"
            cv2.imwrite(result_filename, image_with_walls)
            self.label_info.config(text=f"Result saved as {result_filename}")

        except ValueError as e:
            self.label_info.config(text=str(e))

def main():
    root = Tk()
    app = MazeSolverApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
