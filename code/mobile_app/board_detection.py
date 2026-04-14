import cv2
import numpy as np

# parameters: Canny - 60, 70; Morph - (15, 15); approxPolyDP - 0.06*perimeter; Gaussian blur - (7, 7)

# parameters: Canny - 60, 80; Morph - (15, 15); approxPolyDP - 0.06*perimeter; Gaussian blur - (7, 7)

# parameters: Canny - 60, 70; Morph - (25, 25); approxPolyDP - 0.06*perimeter; Gaussian blur - (7, 7)

# parameters: Canny - 40, 55; Morph - (11, 11); approxPolyDP - 0.06*perimeter; Gaussian blur - (9, 9)

# parameters: Canny - 30, 55; Morph - (9, 9); approxPolyDP - 0.06*perimeter; Gaussian blur - (9, 9)

# parameters: Canny - 32, 55; Morph - (7, 7); approxPolyDP - 0.06*perimeter; Gaussian blur - (9, 9) # ! 

# parameters: Canny - 23, 55; Morph - (7, 7); approxPolyDP - 0.06*perimeter; Gaussian blur - (9, 9)

# parameters: Canny - 25, 55; Morph - (9, 9); approxPolyDP - 0.06*perimeter; Gaussian blur - (9, 9); fg_threshold_ratio - 0.01 # !

# parameters: Canny - 25, 55; Morph - (9, 9); approxPolyDP - 0.06*perimeter; Gaussian blur - (9, 9); fg_threshold_ratio - 0.006

def detect_board_old(image):
    """
    Method detects board as largest rectangle in the image using Canny, morphological operations and finding contours.
    
    :param image: image, can be both grayscale and RGB 
    :return: array of shape (4, 2) containing the ordered coordinates of the corners of the detected board
    """
    # resize image so the bigger dimension is 1000px
    height, width = image.shape[:2]
    scale = 1.0
    if max(height, width) > 1000:
        scale = 1000 / max(height, width)
        image = cv2.resize(image, (int(width * scale), int(height * scale)))

    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) # convert to grayscale
    blurred_img = cv2.GaussianBlur(gray_img, (9, 9), 0) # reduce noise; 0 means that the standard deviation is calculated based on the kernel size # ! (7, 7)
    edges = cv2.Canny(blurred_img, 30, 55) # ! 50, 100 # detect edges, retuerns binary image with edges marked as white pixels

    # Close gaps in edges
    # NOTE: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)) # ! cv2.MORPH_RECT, (29, 29) // (15, 15) // (25, 25)
    # MORPH_CLOSE = dilation followed by erosion, fills small holes in edges and connects nearby edge segments
    closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # RETR_EXTERNAL - only outer contours, CHAIN_APPROX_SIMPLE to compress collinear points
    # border-following algorithm
    # NOTE: Suzuki-Abe algorithm for hierarchy
    # NOTE: https://docs.opencv.org/4.x/d4/d73/tutorial_py_contours_begin.html
    contours = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2] # shape (N, 1, 2) -> N points (x, y)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    min_area = 0.1 * image.shape[0] * image.shape[1]
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        perimeter = cv2.arcLength(cnt, True)
        # NOTE: https://docs.opencv.org/4.x/dd/d49/tutorial_py_contour_features.html
        approx = cv2.approxPolyDP(cnt, 0.06*perimeter, True)

        # ! show closed edges for debugging
        # cv2.imshow("Original image", image)
        # cv2.imshow("Blurred", blurred_img)
        cv2.imshow("Edges", edges)
        cv2.imshow("Closed Edges", closed_edges)
        # ! show all the contours for debugging
        debug_img = image.copy()
        cv2.drawContours(debug_img, contours, -1, (0, 255, 0), 2)
        cv2.imshow("Contours", debug_img)
        # cv2.waitKey(0)
        # ! show approximated contour for debugging
        debug_img = image.copy()
        cv2.drawContours(debug_img, [cnt], -1, (255, 0, 0), 2) # DB blue
        cv2.drawContours(debug_img, [approx], -1, (0, 255, 0), 2) # LG green
        cv2.imshow("Approximated Contour", debug_img)
        cv2.waitKey(0)

        # scale back to original image size
        approx = (approx / scale).astype(np.float32)
        if len(approx) == 4:
            return order_points(approx.reshape(4, 2))

    raise RuntimeError("Board not found")


def order_points(points:np.ndarray) -> np.ndarray:
    """
    Method takes 4 points of a trapeze and orders them in consistent way so that the longest side comes to the bottom.
    Method assumes that the points are in clockwise or counterclockwise order, but does not assume any specific starting point.

    :param points: array of shape (4, 2) containing the coordinates of the corners of the trapeze
    :return: array of shape (4, 2) containing the ordered coordinates of the corners
    """
    rect = np.zeros((4, 2), dtype="float32")

    center = np.mean(points, axis=0)
    angles = np.arctan2(points[:,1] - center[1], points[:,0] - center[0])

    points = points[np.argsort(angles)]
    
    # find the longest side to determine orientation
    longest_dist = 0
    first_point = None
    for i in range(4):
        p1 = points[i]
        p2 = points[(i + 1) % 4]
        dists = np.linalg.norm(p2 - p1)
        if dists > longest_dist:
            longest_dist = dists
            first_point = i

    points = np.roll(points, -first_point-2, axis=0)

    rect[0] = points[0]
    rect[1] = points[1]
    rect[2] = points[2]
    rect[3] = points[3]

    return rect


# blur: (9, 9); Canny: 20, 55; Morph: (7, 7); 
# Hough: threshold=60, minLineLength=80, maxLineGap=20; 
# merge_similar_hough_lines: angle_tol_deg=2.0, rho_tol_px=8.0; 
# keep_longest_line_in_clusters: angle_tol_deg=3, rho_tol_px=64.0

# blur: (11, 11); Canny: 25, 55; Morph: (7, 7); 
# Hough: threshold=60, minLineLength=30, maxLineGap=20; 
# merge_similar_hough_lines: angle_tol_deg=2.0, rho_tol_px=8.0; 
# keep_longest_line_in_clusters: angle_tol_deg=3, rho_tol_px=12.0
# approxPolyDP

# ! ove rade
# blur: (11, 11); Canny: 25, 55; Morph: (7, 7); 
# Hough: threshold=60, minLineLength=30, maxLineGap=20; 
# merge_similar_hough_lines: angle_tol_deg=1.5, rho_tol_px=2.0; 
# keep_longest_line_in_clusters: angle_tol_deg=3.0, rho_tol_px=10.0
# approxPolyDP

# blur: (11, 11); Canny: 25, 55; Morph: (7, 7); # !
# Hough: threshold=60, minLineLength=30, maxLineGap=10; 
# merge_similar_hough_lines: angle_tol_deg=1.5, rho_tol_px=2.2; 
# keep_longest_line_in_clusters: angle_tol_deg=3.0, rho_tol_px=13.0
# approxPolyDP - disabled

# blur: (11, 11); Canny: 22, 55; Morph: (9, 9); 
# Hough: threshold=60, minLineLength=30, maxLineGap=10; 
# merge_similar_hough_lines: angle_tol_deg=1.0, rho_tol_px=2.2; 
# keep_longest_line_in_clusters: angle_tol_deg=3.0, rho_tol_px=13.0
# approxPolyDP - disabled

# blur: (11, 11); Canny: 25, 55; Morph: (7, 7); # !
# Hough: threshold=80, minLineLength=40, maxLineGap=10; 
# merge_similar_hough_lines: angle_tol_deg=1.5, rho_tol_px=2.2; 
# keep_longest_line_in_clusters: angle_tol_deg=3.0, rho_tol_px=13.0
# approxPolyDP - disabled

def detect_board(image):
    """
    Method detects board as largest rectangle in the image.

    Steps in detection:
        1. resizing on fixed size
        2. Canny edge detection
        3. morphological closing to connect nearby edge segments
        4. finding contours and selecting the largest one
        5. creating a binary mask of the contour
        6. Hough transformation to find lines in the contour
        7. merging similar lines to get more stable results
        8. keeping only the longest line in each cluster of similar lines to get more stable results
        9. finding intersection points of the 4 longest lines

    :param image: image, can be both grayscale and RGB
    :return: array of shape (4, 2) containing the ordered coordinates of the corners of the detected board
    """
    # resize image so the bigger dimension is 1000px
    height, width = image.shape[:2]
    scale = 1.0
    if max(height, width) > 1000:
        scale = 1000 / max(height, width)
        image = cv2.resize(image, (int(width * scale), int(height * scale)))

    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) # convert to grayscale
    blurred_img = cv2.GaussianBlur(gray_img, (11, 11), 0) # reduce noise; 0 means that the standard deviation is calculated based on the kernel size # ! (7, 7)
    edges = cv2.Canny(blurred_img, 25, 55) # ! 50, 100 # detect edges, retuerns binary image with edges marked as white pixels

    # Close gaps in edges
    # NOTE: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)) # ! cv2.MORPH_RECT, (29, 29) // (15, 15) // (25, 25)
    # MORPH_CLOSE = dilation followed by erosion, fills small holes in edges and connects nearby edge segments
    # closed_edges = edges.copy()
    closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # RETR_EXTERNAL - only outer contours, CHAIN_APPROX_SIMPLE to compress collinear points
    # border-following algorithm
    # NOTE: Suzuki-Abe algorithm for hierarchy
    # NOTE: https://docs.opencv.org/4.x/d4/d73/tutorial_py_contours_begin.html
    contours = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2] # shape (N, 1, 2) -> N points (x, y)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    cnt = contours[0]
    # cnt = cv2.approxPolyDP(cnt, 0.0005*cv2.arcLength(cnt, True), True)
    # binary mask of the contour shilhouette
    mask = np.zeros_like(gray_img)
    cv2.drawContours(mask, [cnt], -1, 255, 1)

    # k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=1)

    # use Hough transformation to find lines in the contour
    lines = cv2.HoughLinesP(mask, 1, 1*np.pi/180, threshold=80, minLineLength=40, maxLineGap=10)
    if lines is None:
        raise RuntimeError("Board not found")
    
    # ! display detected lines for debugging
    # line_img = image.copy()
    # for line in lines:
    #     x1, y1, x2, y2 = line[0]
    #     cv2.line(line_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    # cv2.imshow("Detected Lines 111", line_img)

    lines = merge_similar_hough_lines(lines, angle_tol_deg=1.5, rho_tol_px=2.2)
    lines = keep_longest_line_in_clusters(lines, angle_tol_deg=3.0, rho_tol_px=13.0)
    # grouped_lines = group_parallel_and_perpendicular_lines(lines, angle_tol_deg=15.0)
    # grouped_lines = sorted(grouped_lines, key=lambda g: g[2], reverse=True)
    # longest_lines = grouped_lines[0][0]
    longest_lines = sorted(lines, key=lambda l: np.linalg.norm([l[0][2] - l[0][0], l[0][3] - l[0][1]]), reverse=True)

    # find intersection points of the 4 longest lines
    intersectons = find_intersections(longest_lines[:4], img_dim=image.shape[:2][::-1])

    # ! display edges and closed edges for debugging
    # cv2.imshow("Edges", edges)
    # cv2.imshow("Closed Edges", closed_edges)
    # # ! display contour mask for debugging
    # cv2.imshow("Contour Mask", mask)
    # # ! display detected lines for debugging
    # line_img = image.copy()
    # for line in lines:
    #     x1, y1, x2, y2 = line[0]
    #     cv2.line(line_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    # cv2.imshow("Detected Lines", line_img)
    # # ! display 4 longest lines for debugging
    # line_img = image.copy()
    # for line in longest_lines[:4]:
    #     x1, y1, x2, y2 = line[0]
    #     cv2.line(line_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
    # # ! display intersection points for debugging
    # for inter in intersectons:
    #     x, y = int(inter[0]), int(inter[1])
    #     cv2.circle(line_img, (x, y), 4, (255, 0, 255), 2)
    # cv2.imshow("Longest Lines & Intersections", line_img)
    # cv2.waitKey(0)

    intersectons = np.array(intersectons)
    intersectons = (intersectons / scale).astype(np.float32)
    if intersectons is not None and len(intersectons) == 4:
        return order_points(intersectons)
    
    raise RuntimeError("Board not found")



def find_intersections(lines, img_dim=(1000, 1000)) -> list[tuple[int, int]]:
    """
    Finds intersection points of given lines.
    Intersections that are outside the image dimensions are ignored.

    :param lines: list of lines in format [[x1, y1, x2, y2]]
    :param img_dim: dimensions of the image in format (width, height) to filter out intersections that are outside the image
    :return: list of intersection points in format [(x, y)]
    """
    if len(lines) < 4:
        raise RuntimeError("Board not found")
    
    intersections = []
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            inter = line_intersection(lines[i][0], lines[j][0])
            # if inter is outside the image, ignore it
            if inter is None or (inter[0] < 0 or inter[0] > img_dim[0] or inter[1] < 0 or inter[1] > img_dim[1]):
                continue
            intersections.append(inter)

    return intersections


def _seg_len(s) -> float:
    """
    Calculates the length of a line segment.

    :param s: line segment in format [x1, y1, x2, y2]
    :return: length of the line segment
    """
    x1, y1, x2, y2 = s
    return float(np.hypot(x2 - x1, y2 - y1))


def _line_params(seg) -> tuple[float, float]:
    """
    Calculates the parameters of a line in normal form n dot x = rho, where n is the normal vector and rho is the distance from the origin.
    The angle of the normal vector is returned in range [0, pi).

    :param seg: line segment in format [x1, y1, x2, y2]
    :return: tuple (theta, rho) where theta is the angle of the normal vector in radians and rho is the distance from the origin
    """
    # direction angle in [0, pi)
    x1, y1, x2, y2 = map(float, seg)
    dx, dy = x2 - x1, y2 - y1
    theta = np.arctan2(dy, dx) % np.pi

    # normal form n dot x = rho with rho >= 0
    n = np.array([-dy, dx], dtype=np.float64)
    n_norm = np.linalg.norm(n)
    if n_norm == 0:
        return theta, 0.0
    n /= n_norm
    rho = n[0] * x1 + n[1] * y1
    if rho < 0:
        rho = -rho
        theta = (theta + np.pi) % np.pi
    return theta, rho


def _angle_diff(a, b) -> float:
    """
    Calculates the smallest difference between two angles (in radians) of a line, result is in range [0, pi).

    :param a: first angle in radians, expected in range [0, pi)
    :param b: second angle in radians, expected in range [0, pi)
    :return: smallest difference between the two angles in radians, in range [0, pi) 
    """
    d = abs(a - b)
    return min(d, np.pi - d)


def cluster_lines_by_angle_and_rho(lines, angle_tol_deg=3.0, rho_tol_px=12.0) -> list[list[tuple[int, int, int, int]]]:
    """
    Clusters lines by angle and rho distance.

    :param lines: array of lines in format [[[x1, y1, x2, y2]], ...]
    :param angle_tol_deg: angle tolerance in degrees for clustering lines, default is 3 degrees
    :param rho_tol_px: rho distance tolerance in pixels for clustering lines, default is 12 pixels
    :param seg_dist_tol: tolerance for distance between line segments in pixels, default is 20 pixels
    :return: list of clusters, where each cluster is a list of line segments in format (x1, y1, x2, y2)
    """
    if lines is None or len(lines) == 0:
        return []

    segs = [tuple(map(int, l[0])) for l in lines]
    segs.sort(key=_seg_len, reverse=True)

    angle_tol = np.deg2rad(angle_tol_deg)
    clusters = []

    for seg in segs:
        th, rh = _line_params(seg)
        placed = False
        for c in clusters:
            diff = _angle_diff(th, c["theta"])
            if diff <= angle_tol and abs(rh - c["rho"]) <= rho_tol_px:
                c["segs"].append(seg)
                # Update orientation mean for axial angles (period pi).
                # Doubling the angle maps opposite directions to same point.
                # Double is used to avoid ambiguity of angles near 0 and pi, which are actually close to each other.
                c["sum_cos2"] += np.cos(2.0 * th)
                c["sum_sin2"] += np.sin(2.0 * th)
                c["theta"] = 0.5 * (np.arctan2(c["sum_sin2"], c["sum_cos2"]) % (2.0 * np.pi))
                c["theta"] %= np.pi
                c["rho"] = (c["rho"] * c["n"] + rh) / (c["n"] + 1)
                c["n"] += 1
                placed = True
                break
        if not placed:
            clusters.append({
                "theta": th,
                "rho": rh,
                "n": 1,
                "segs": [seg],
                "sum_cos2": np.cos(2.0 * th),
                "sum_sin2": np.sin(2.0 * th),
            })

    return clusters


def merge_similar_hough_lines(lines, angle_tol_deg=3.0, rho_tol_px=12.0) -> np.ndarray:
    """
    Clusters near-duplicate lines by orientation and rho distance.
    Clusters are then merged into one long line segment along the cluster direction.
    Merging is done by taking the clusters direction and center of all endpoints of the lines in the cluster.
    Direction and center are then used to find parameters of the merged line, which is then extended to the extremes of the endpoints in the cluster.
    
    :param lines: array of lines in format [[[x1, y1, x2, y2]], ...]
    :param angle_tol_deg: angle tolerance in degrees for clustering lines, default is 3 degrees
    :param rho_tol_px: rho distance tolerance in pixels for clustering lines, default is 12 pixels
    :return: array of merged lines in format [[[x1, y1, x2, y2]], ...]
    """
    clusters = cluster_lines_by_angle_and_rho(lines, angle_tol_deg, rho_tol_px)

    # Merge each cluster into one long segment along cluster direction
    merged = []
    for c in clusters:
        pts = np.array([(s[0], s[1]) for s in c["segs"]] + [(s[2], s[3]) for s in c["segs"]], dtype=np.float64)
        center = pts.mean(axis=0)
        u = np.array([np.cos(c["theta"]), np.sin(c["theta"])], dtype=np.float64)  # unit direction
        
        # get extremes in both axis
        x_max = pts[:,0].max()
        x_min = pts[:,0].min()
        y_max = pts[:,1].max()
        y_min = pts[:,1].min()

        # get line parameters from center and u
        # y = ax + b
        if abs(u[0]) >= abs(u[1]):
            a = u[1] / u[0]
            b = center[1] - a * center[0]
            p1 = np.array([x_min, a * x_min + b])
            p2 = np.array([x_max, a * x_max + b])
        # x = ay + b
        else:
            a = u[0] / u[1]
            b = center[0] - a * center[1]
            p1 = np.array([a * y_min + b, y_min])
            p2 = np.array([a * y_max + b, y_max])
        merged.append([[int(round(p1[0])), int(round(p1[1])), int(round(p2[0])), int(round(p2[1]))]])

    return np.array(merged, dtype=np.int32)


def keep_longest_line_in_clusters(lines, angle_tol_deg=2.0, rho_tol_px=8.0) -> np.ndarray:
    """
    Cluster near-duplicate lines by orientation and rho distance and keep only the longest segment from each cluster.

    :param lines: array of lines in format [[[x1, y1, x2, y2]], ...]
    :param angle_tol_deg: angle tolerance in degrees for clustering lines, default is 2 degrees
    :param rho_tol_px: rho distance tolerance in pixels for clustering lines, default is 8 pixels
    :return: array of lines in format [[[x1, y1, x2, y2]], ...] where only the longest line from each cluster of similar lines is kept
    """
    clusters = cluster_lines_by_angle_and_rho(lines, angle_tol_deg, rho_tol_px)

    longest_per_cluster = []
    for c in clusters:
        longest = max(c["segs"], key=_seg_len)
        longest_per_cluster.append([[longest[0], longest[1], longest[2], longest[3]]])

    return np.array(longest_per_cluster, dtype=np.int32)


# ! remove
def group_parallel_and_perpendicular_lines(lines, angle_tol_deg=15.0) -> list[tuple[list[tuple[int, int, int, int]], float]]:
    # group lines that are parallel or perpendicular to each other, return list of groups with their total line length
    groups = []
    tol_rad = np.deg2rad(angle_tol_deg)
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.arctan2(y2 - y1, x2 - x1) % np.pi
        length = _seg_len(line[0])
        placed = False
        for g in groups:
            if _angle_diff(angle, g[1]) <= tol_rad or _angle_diff(angle, (g[1] + np.pi/2) % np.pi) <= tol_rad:
                g[0].append(line)
                g[2] += length
                placed = True
                break
        if not placed:
            groups.append([[line], angle, length])

    for group in groups:
        # check if there are at least 2 parralel and 2 perpendicular lines in the group, if not, remove the group
        parallel_lines = 0
        perpendicular_lines = 0
        for line in group[0]:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) % np.pi
            if _angle_diff(angle, group[1]) <= tol_rad:
                parallel_lines += 1
            elif _angle_diff(angle, (group[1] + np.pi/2) % np.pi) <= tol_rad:
                perpendicular_lines += 1

        if parallel_lines < 2 or perpendicular_lines < 2:
            group[2] = 0.0
    return groups


def line_intersection(l1, l2) -> np.ndarray | None:
    """
    Finds the intersection point of two lines given in format [x1, y1, x2, y2].
    If the lines are parallel, returns None.

    :param l1: first line in format [x1, y1, x2, y2]
    :param l2: second line in format [x1, y1, x2, y2]
    :return: intersection point in format [x, y] or None if lines are parallel
    """
    x1,y1,x2,y2 = l1
    x3,y3,x4,y4 = l2

    A1 = y2 - y1
    B1 = x1 - x2
    C1 = A1*x1 + B1*y1

    A2 = y4 - y3
    B2 = x3 - x4
    C2 = A2*x3 + B2*y3

    det = A1*B2 - A2*B1
    if det == 0:
        return None

    x = (B2*C1 - B1*C2) / det
    y = (A1*C2 - A2*C1) / det
    return np.array([x,y])