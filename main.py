import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np
import networkx as nx
from shapely.geometry import LineString

class EvacuationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikacja Ewakuacyjna")

        # GUI
        self.btn_open_image = tk.Button(root, text="Wczytaj plan ewakuacyjny", command=self.open_image)
        self.btn_open_image.pack(pady=10)

        # Panel obrazu
        self.canvas = tk.Canvas(root)
        self.canvas.pack()

        # Model detekcji obiektów przy pomocy OpenCV
        self.object_detection_model = cv2

        # Algorytm grafowy do wyznaczania ścieżek
        self.graph = nx.Graph()
        
    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
    
        if file_path:
            # Wczytujemy obraz przy użyciu OpenCV
            image = cv2.imread(file_path)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # OpenCV używa formatu BGR, a PIL oczekuje RGB

            # Detekcja obiektów
            objects = self.detect_objects(image)

            # Wyznaczanie ścieżek ewakuacyjnych
            evacuation_paths = self.calculate_evacuation_paths(objects)

            # Wizualizacja detekcji na obrazie
            for obj in objects:
                cv2.rectangle(image_rgb, obj["bbox"][0], obj["bbox"][1], (0, 255, 0), 2)

            # Rysowanie ścieżek ewakuacyjnych na obrazie
            for start_node, paths in evacuation_paths.items():
                for end_node, path in paths.items():
                    if start_node != end_node:
                        cv2.line(image_rgb, start_node, path[1], (255, 0, 0), 2)

            # Przekształcanie obrazu do obiektu ImageTk
            image = Image.fromarray(image_rgb)
            image_tk = ImageTk.PhotoImage(image)

             # Wyświetl obraz na canvas
            self.canvas.config(width=image.width, height=image.height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=image_tk)
            self.canvas.image = image_tk

            
    def detect_objects(self, image):
        # Algorytm Canny'ego do detekcji krawędzi
        edges = cv2.Canny(image, 100, 200)

        # Szukanie konturów na podstawie krawędzi
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        objects = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            objects.append({"bbox": [(x, y), (x + w, y + h)]})

        return objects

    def calculate_evacuation_paths(self, objects):
    # Dodawanie wierzchołków reprezentujących środki obiektów
        for obj in objects:
            center = ((obj["bbox"][0][0] + obj["bbox"][1][0]) // 2, (obj["bbox"][0][1] + obj["bbox"][1][1]) // 2)
            self.graph.add_node(center)

        # Dodawanie krawędzi między sąsiadującymi obiektami
        for i in range(len(objects)):
            for j in range(i + 1, len(objects)):
                obj1 = objects[i]
                obj2 = objects[j]
                center1 = ((obj1["bbox"][0][0] + obj1["bbox"][1][0]) // 2, (obj1["bbox"][0][1] + obj1["bbox"][1][1]) // 2)
                center2 = ((obj2["bbox"][0][0] + obj2["bbox"][1][0]) // 2, (obj2["bbox"][0][1] + obj2["bbox"][1][1]) // 2)

                line = LineString([center1, center2])
                line_intersects = False
                for edge in self.graph.edges:
                    if LineString(edge).intersects(line):
                        line_intersects = True
                        break

                if not line_intersects:
                    self.graph.add_edge(center1, center2, weight=line.length)

        evacuation_paths = {}
        for start_node in self.graph.nodes:
            paths = nx.single_source_dijkstra_path(self.graph, start_node, weight='weight')
            evacuation_paths[start_node] = paths

        return evacuation_paths
    
    def draw_evacuation_paths(self, image, evacuation_paths):
        for start_node, paths in evacuation_paths.items():
            for end_node, path in paths.items():
                if start_node != end_node:
                    for i in range(len(path)-1):
                        cv2.line(image, path[i], path[i+1], (255, 0, 0), 2)  # Rysowanie ścieżki na obrazie

        return image
    
    def show_image_on_canvas(self, image):
        # Przekształcanie obrazu do obiektu ImageTk
        image = Image.fromarray(image)
        image_tk = ImageTk.PhotoImage(image)

        # Wyświetlanie obrazu na canvas
        self.canvas.config(width=image.width, height=image.height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=image_tk)
        self.canvas.image = image_tk

if __name__ == "__main__":
    root = tk.Tk()
    app = EvacuationApp(root)
    root.mainloop()
