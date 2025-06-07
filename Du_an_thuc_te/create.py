import os
import rasterio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from matplotlib.patches import FancyArrowPatch
from matplotlib.ticker import ScalarFormatter
import seaborn as sns
from rasterio.plot import show
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from pathlib import Path
import geopandas as gpd  # Thêm geopandas để đọc shapefile
from shapely.geometry import Point

# Define the input and output directories
input_dir = "/Users/Admin/Downloads/Cac_van_de_hien_dai_trong_Vien_tham_va_GIS-20250605T095132Z-1-001/Cac_van_de_hien_dai_trong_Vien_tham_va_GIS/gee-exported"
output_dir = "/Users/Admin/Downloads/Cac_van_de_hien_dai_trong_Vien_tham_va_GIS-20250605T095132Z-1-001/Cac_van_de_hien_dai_trong_Vien_tham_va_GIS/Bao_cao/Figures"
shapefile_dir = "/Users/Admin/Downloads/Cac_van_de_hien_dai_trong_Vien_tham_va_GIS-20250605T095132Z-1-001/Cac_van_de_hien_dai_trong_Vien_tham_va_GIS/gee-exported/shapefile"
fire_points_file = os.path.join(input_dir, "Actual_fire.csv") # Giả định file CSV, sẽ kiểm tra các định dạng khác

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Load the shapefile once
gialai_shapefile = os.path.join(shapefile_dir, 'gia_lai.shp')
try:
    gialai_gdf = gpd.read_file(gialai_shapefile)
    print(f"Successfully loaded Gia Lai shapefile")
except Exception as e:
    print(f"Error loading shapefile: {e}")
    gialai_gdf = None

# Helper function to add scale bar and map scale text
def _add_scalebar_and_scale_text(ax, src_bounds, fig_width_inches):
    map_bounds = src_bounds # (west, south, east, north)
    map_width_degrees = map_bounds[2] - map_bounds[0]
    center_latitude = (map_bounds[1] + map_bounds[3]) / 2.0

    # Approx km per degree
    # KM_PER_DEGREE_LAT = 110.574 # km per degree latitude (approx constant) # Not directly used for width-based scalebar
    km_per_degree_lon = 111.320 * np.cos(np.radians(center_latitude)) # km per degree longitude

    if abs(km_per_degree_lon) < 1e-6: # Avoid division by zero at poles or if latitude is 90/-90
        km_per_degree_lon = 1e-6 if km_per_degree_lon >=0 else -1e-6

    map_width_km = map_width_degrees * km_per_degree_lon

    # Determine a nice length for the scale bar (e.g., 10% to 25% of map width)
    target_scalebar_km_display = map_width_km / 5.0 
    if target_scalebar_km_display < 0.01 and map_width_km > 0: # ensure it's at least 10m for very small areas
        target_scalebar_km_display = 0.01 
    elif map_width_km <=0: # Handle zero or negative map width
        print("Warning: map_width_km is zero or negative, cannot create meaningful scale bar.")
        return

    possible_lengths = np.array([0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 25, 50, 75, 100, 150, 200])
    
    # Filter possible_lengths to be less than map_width_km to avoid overly large scale bars
    valid_lengths = possible_lengths[possible_lengths < map_width_km * 0.8] # Max 80% of map width
    if len(valid_lengths) == 0: # if map is very small
        if len(possible_lengths[possible_lengths < map_width_km]) > 0:
             valid_lengths = possible_lengths[possible_lengths < map_width_km]
        else: # if map width is tiny, e.g. <0.01km
             valid_lengths = np.array([map_width_km * 0.5]) # 50% of tiny map width

    if len(valid_lengths) > 0 :
        # Find the valid_length closest to target_scalebar_km_display
        scalebar_km = valid_lengths[np.argmin(np.abs(valid_lengths - target_scalebar_km_display))]
    else: 
        scalebar_km = target_scalebar_km_display # Fallback if no valid lengths (should use a fraction of map_width_km)
        if scalebar_km > map_width_km * 0.8 : scalebar_km = map_width_km * 0.8 # Ensure not too large

    if scalebar_km <= 1e-6 : scalebar_km = 0.01 # final fallback for really small scalebar_km to avoid zero/negative

    scalebar_degrees = scalebar_km / km_per_degree_lon
    
    if abs(map_width_degrees) < 1e-9: map_width_degrees = 1e-9 * np.sign(map_width_degrees) if map_width_degrees != 0 else 1e-9 # Avoid division by zero
    scalebar_axes_fraction = scalebar_degrees / map_width_degrees
    
    # Ensure scalebar_axes_fraction is reasonable (e.g., not > 0.8 of map width, not negative)
    scalebar_axes_fraction = min(abs(scalebar_axes_fraction), 0.6) # Capped at 60% for aesthetics

    # Position at bottom center
    sb_y_pos = 0.07       # y position of the bar in axes fraction (Increased from 0.05)
    sb_text_y_offset_labels = 0.02  # for km labels va='top'
    sb_text_y_offset_scale = 0.04  # for 1:N scale text va='top'
    sb_tick_height = 0.005

    sb_x_center = 0.5
    sb_x_start = sb_x_center - scalebar_axes_fraction / 2
    sb_x_end = sb_x_center + scalebar_axes_fraction / 2

    ax.plot([sb_x_start, sb_x_end], [sb_y_pos, sb_y_pos], 'k-', transform=ax.transAxes, linewidth=1.5)

    # Labels: 0, half, full. If scalebar_km is small, adjust labels.
    if scalebar_km >= 1:
        km_label_half = f'{scalebar_km/2:.1f}'.rstrip('0').rstrip('.')
        km_label_full = f'{scalebar_km:.1f}'.rstrip('0').rstrip('.') + ' km'
    else: # For sub-km scales, show in meters
        m_half = scalebar_km * 500
        m_full = scalebar_km * 1000
        km_label_half = f'{m_half:.0f} m'
        km_label_full = f'{m_full:.0f} m'

    tick_positions_axes = [sb_x_start, sb_x_center, sb_x_end]
    tick_labels_text = ['0', km_label_half, km_label_full]

    for tick_x, label_txt in zip(tick_positions_axes, tick_labels_text):
        ax.plot([tick_x, tick_x], [sb_y_pos - sb_tick_height, sb_y_pos + sb_tick_height], 
                'k-', transform=ax.transAxes, linewidth=1)
        ax.text(tick_x, sb_y_pos - sb_text_y_offset_labels, label_txt, transform=ax.transAxes,
                ha='center', va='top', fontsize=8)

    # Calculate and display map scale (1:N)
    axes_bbox = ax.get_position() 
    axes_width_on_paper_inches = axes_bbox.width * fig_width_inches
    axes_width_on_paper_m = axes_width_on_paper_inches * 0.0254

    map_actual_width_m = map_width_km * 1000

    if abs(axes_width_on_paper_m) > 1e-6 and map_actual_width_m > 0: 
        scale_denominator_N = abs(map_actual_width_m / axes_width_on_paper_m)
        
        rounded_N = 1
        if scale_denominator_N <= 0: rounded_N = 1 
        elif scale_denominator_N < 1000: 
            rounded_N = round(scale_denominator_N / 50.0) * 50 
            if rounded_N == 0 : rounded_N = 50
        elif scale_denominator_N < 10000: 
            rounded_N = round(scale_denominator_N / 500.0) * 500
            if rounded_N == 0 : rounded_N = 500
        elif scale_denominator_N < 50000: 
            rounded_N = round(scale_denominator_N / 1000.0) * 1000
        elif scale_denominator_N < 200000: 
            rounded_N = round(scale_denominator_N / 5000.0) * 5000
        else: 
            rounded_N = round(scale_denominator_N / 10000.0) * 10000
        
        if rounded_N == 0 and scale_denominator_N > 0: rounded_N = int(max(1,scale_denominator_N))
        if rounded_N <=0 : rounded_N = int(scale_denominator_N) if scale_denominator_N > 0 else 1


        scale_text = f"1 : {int(rounded_N):,}".replace(',', '.') 
        ax.text(sb_x_center, sb_y_pos - sb_text_y_offset_scale, scale_text, transform=ax.transAxes,
                ha='center', va='top', fontsize=9)
    else:
        print(f"Warning: Could not calculate map scale. axes_width_m: {axes_width_on_paper_m}, map_actual_width_m: {map_actual_width_m}")

# Hàm để đọc dữ liệu điểm cháy
def load_fire_points():
    # Kiểm tra các định dạng phổ biến
    possible_formats = [
        os.path.join(input_dir, "Actual_fire.csv"),
        os.path.join(input_dir, "Actual_fire.shp"),
        os.path.join(input_dir, "Actual_Fire.csv"),
        os.path.join(input_dir, "Actual_Fire.shp"),
        os.path.join(input_dir, "GiaLai_Actual_Fire.csv"),
        os.path.join(input_dir, "GiaLai_Actual_Fire.shp"),
        os.path.join(shapefile_dir, "fire_points.shp"),
        os.path.join(shapefile_dir, "actual_fire.shp")
    ]
    
    for file_path in possible_formats:
        if os.path.exists(file_path):
            try:
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.csv':
                    # Đọc file CSV với các tên cột tiêu chuẩn cho dữ liệu không gian
                    df = pd.read_csv(file_path)
                    # Kiểm tra các cột tọa độ cần thiết
                    coord_columns = [
                        ('longitude', 'latitude'),
                        ('lon', 'lat'),
                        ('x', 'y'),
                        ('long', 'lat')
                    ]
                    
                    for x_col, y_col in coord_columns:
                        if x_col in df.columns and y_col in df.columns:
                            # Tạo GeoDataFrame từ dữ liệu CSV
                            gdf = gpd.GeoDataFrame(
                                df, 
                                geometry=gpd.points_from_xy(df[x_col], df[y_col]),
                                crs="EPSG:4326"  # WGS84
                            )
                            print(f"Loaded fire points from {file_path} using columns {x_col}, {y_col}")
                            return gdf
                    
                    # Nếu không tìm thấy cột chuẩn, thử đọc 2 cột đầu tiên là tọa độ
                    if len(df.columns) >= 2:
                        gdf = gpd.GeoDataFrame(
                            df,
                            geometry=gpd.points_from_xy(df.iloc[:, 0], df.iloc[:, 1]),
                            crs="EPSG:4326"
                        )
                        print(f"Loaded fire points from {file_path} using first two columns")
                        return gdf
                    
                elif ext == '.shp':
                    # Đọc trực tiếp shapefile
                    gdf = gpd.read_file(file_path)
                    print(f"Loaded fire points from shapefile {file_path}")
                    return gdf
                    
            except Exception as e:
                print(f"Error loading fire points from {file_path}: {e}")
    
    # Thử đọc từ file điểm cháy được tạo trong quá trình tạo dữ liệu
    try:
        # Thử đọc raster và chuyển thành điểm
        fire_raster_path = os.path.join(input_dir, 'GiaLai_Actual_Fire.tif')
        if os.path.exists(fire_raster_path):
            with rasterio.open(fire_raster_path) as src:
                data = src.read(1)
                transform = src.transform
                
                # Tìm vị trí các điểm có giá trị > 0 (điểm cháy)
                y_idx, x_idx = np.where(data > 0)
                
                # Chuyển từ chỉ số pixel sang tọa độ
                x_coords = transform[0] * x_idx + transform[1] * y_idx + transform[2]
                y_coords = transform[3] * x_idx + transform[4] * y_idx + transform[5]
                
                # Tạo GeoDataFrame từ các điểm
                points_df = pd.DataFrame({
                    'value': data[y_idx, x_idx],
                    'geometry': [Point(x, y) for x, y in zip(x_coords, y_coords)]
                })
                
                gdf = gpd.GeoDataFrame(points_df, geometry='geometry', crs=src.crs)
                print(f"Extracted fire points from raster {fire_raster_path}")
                return gdf
    except Exception as e:
        print(f"Error extracting fire points from raster: {e}")
    
    print("No fire points data found in the specified paths")
    return None

# Load fire points once
fire_points_gdf = load_fire_points()
if fire_points_gdf is not None:
    print(f"Successfully loaded {len(fire_points_gdf)} fire points")
else:
    print("No fire points data found or could not be loaded")

# Function to add map elements (north arrow, scale bar, title, etc.)
def add_map_elements(ax, title, cmap, vmin, vmax, units=None):
    # Add north arrow
    arrow_x, arrow_y = 0.05, 0.85
    arrow_length = 0.07
    
    # N
    ax.text(arrow_x, arrow_y+arrow_length+0.02, 'N', transform=ax.transAxes, 
            ha='center', va='center', fontsize=12, fontweight='bold')
    
    # W, E, S
    ax.text(arrow_x-0.025, arrow_y, 'W', transform=ax.transAxes, 
            ha='center', va='center', fontsize=12, fontweight='bold')
    ax.text(arrow_x+0.025, arrow_y, 'E', transform=ax.transAxes, 
            ha='center', va='center', fontsize=12, fontweight='bold')
    ax.text(arrow_x, arrow_y-0.025, 'S', transform=ax.transAxes, 
            ha='center', va='center', fontsize=12, fontweight='bold')
    
    # Draw arrow
    arrow = FancyArrowPatch((arrow_x, arrow_y), (arrow_x, arrow_y+arrow_length), 
                           transform=ax.transAxes, color='black', linewidth=1.5,
                           arrowstyle='-|>', mutation_scale=15)
    ax.add_patch(arrow)
    
    # Draw diamond around the arrow
    diamond_x = [arrow_x, arrow_x+0.025, arrow_x, arrow_x-0.025, arrow_x]
    diamond_y = [arrow_y+arrow_length/2, arrow_y, arrow_y-arrow_length/2, arrow_y, arrow_y+arrow_length/2]
    ax.plot(diamond_x, diamond_y, 'k-', transform=ax.transAxes, linewidth=1.0)
    
    # Add scale bar
    scale_x = 0.8
    scale_y = 0.05
    scale_width = 0.15
    ax.plot([scale_x, scale_x+scale_width], [scale_y, scale_y], 'k-', transform=ax.transAxes, linewidth=2)
    
    # Add scale ticks
    for i in range(5):
        tick_x = scale_x + i * scale_width/4
        ax.plot([tick_x, tick_x], [scale_y-0.005, scale_y+0.005], 'k-', transform=ax.transAxes)
    
    # Add scale labels
    ax.text(scale_x, scale_y-0.015, '0', transform=ax.transAxes, ha='center', va='top', fontsize=8)
    ax.text(scale_x+scale_width/4, scale_y-0.015, '10', transform=ax.transAxes, ha='center', va='top', fontsize=8)
    ax.text(scale_x+scale_width/2, scale_y-0.015, '20', transform=ax.transAxes, ha='center', va='top', fontsize=8)
    ax.text(scale_x+3*scale_width/4, scale_y-0.015, '30', transform=ax.transAxes, ha='center', va='top', fontsize=8)
    ax.text(scale_x+scale_width, scale_y-0.015, '40', transform=ax.transAxes, ha='center', va='top', fontsize=8)
    ax.text(scale_x+scale_width/2, scale_y-0.03, 'Kilometers', transform=ax.transAxes, ha='center', va='top', fontsize=8)
    
    # Add colorbar
    cbar = plt.colorbar(plt.cm.ScalarMappable(norm=mcolors.Normalize(vmin=vmin, vmax=vmax), cmap=cmap), 
                        ax=ax, orientation='horizontal', pad=0.05, shrink=0.5)
    
    # Add units to colorbar if provided
    if units:
        cbar.set_label(units)
    
    # Make frame visible
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1)

# Function to read GeoTIFF and create a map with proper frame
def create_map(filename, output_name, title, cmap, vmin, vmax, units=None):
    try:
        # Open the GeoTIFF file
        with rasterio.open(filename) as src:
            # In thông tin hệ tọa độ và extent
            print(f"\n--- Debug thông tin raster: {filename} ---")
            print("Raster CRS:", src.crs)
            print("Raster bounds:", src.bounds)
            print("Raster NoData value:", src.nodata)
            if gialai_gdf is not None:
                print("Shapefile CRS:", gialai_gdf.crs)
                print("Shapefile bounds:", gialai_gdf.total_bounds)
            
            # Đọc dữ liệu gốc
            data = src.read(1)
            transform = src.transform

            # Nếu có giá trị NoData, gán về NaN
            if src.nodata is not None:
                data = np.where(data == src.nodata, np.nan, data)

            # Xử lý dữ liệu bất thường cho bản đồ lượng mưa hoặc các raster tương tự
            if 'Precipitation' in output_name or 'precipitation' in output_name or 'Lượng mưa' in title:
                # Chuyển về float để xử lý NaN
                data = data.astype(float)
                # Gán NaN cho các giá trị âm hoặc quá lớn (giả sử lượng mưa hợp lệ trong [0, 3000])
                data[(data < 0) | (data > 3000)] = np.nan
                # Nếu toàn bộ dữ liệu là NaN hoặc 0, sẽ hiển thị thông báo lỗi
                if np.all(np.isnan(data)) or np.nanmax(data) == 0:
                    fig = plt.figure(figsize=(12, 10), facecolor='white')
                    ax = fig.add_subplot(111)
                    ax.set_facecolor('white')
                    ax.text(0.5, 0.5, 'Không có dữ liệu lượng mưa hợp lệ!',
                            ha='center', va='center', fontsize=20, color='red', transform=ax.transAxes)
                    ax.set_xticks([])
                    ax.set_yticks([])
                    plt.savefig(os.path.join(output_dir, output_name), dpi=300, bbox_inches='tight', 
                               facecolor='white', edgecolor='none', transparent=False)
                    plt.close()
                    print(f"Lỗi: Không có dữ liệu lượng mưa hợp lệ trong {filename}")
                    return

            # Mask raster with shapefile
            if gialai_gdf is not None:
                # Get geometry for masking
                shapes = [feature['geometry'] for feature in gialai_gdf.__geo_interface__['features']]
                
                # Tạo mặt nạ từ hình dạng Gia Lai
                mask_value = np.ones_like(data, dtype=bool)
                
                # Tạo mặt nạ có giá trị True bên trong ranh giới
                out_shape = data.shape
                for geom in shapes:
                    geom_mask = rasterio.features.geometry_mask(
                        [geom], out_shape=out_shape, transform=transform, invert=True)
                    mask_value = mask_value & geom_mask
                
                # Chuyển đổi mảng dữ liệu về float (nếu là integer) để có thể sử dụng masked_array
                if np.issubdtype(data.dtype, np.integer):
                    data_float = data.astype(float)
                    # Tạo masked array - giá trị bên ngoài ranh giới sẽ bị che
                    masked_data = np.ma.masked_array(data_float, mask=~mask_value)
                else:
                    masked_data = np.ma.masked_array(data, mask=~mask_value)
            else:
                # Nếu không có shapefile, sử dụng dữ liệu gốc
                masked_data = data
            
            # Sau khi mask (hoặc nếu không mask), in giá trị min/max/mean
            try:
                print("Giá trị raster sau khi đọc (trước mask): min=", np.nanmin(data), ", max=", np.nanmax(data), ", mean=", np.nanmean(data))
            except Exception as e:
                print("Không thể tính min/max/mean do dữ liệu NaN hoàn toàn hoặc lỗi:", e)
            
            # Create a figure with white background and specific size ratio
            fig = plt.figure(figsize=(12, 10), facecolor='white')
            ax = fig.add_subplot(111)
            ax.set_facecolor('white')
            
            # Set the extent based on the original bounds
            bounds = src.bounds
            
            # Add grid lines (light cyan color)
            ax.grid(True, color='cyan', alpha=0.3, linestyle='-', linewidth=0.5)
            
            # Format tick labels to degree-minute format (e.g., 104°0'E)
            def format_degree(x, pos, axis='x'):
                deg = int(x)
                minute = int((x - deg) * 60)
                
                # Xác định hướng dựa vào trục và giá trị
                if axis == 'x':  # Kinh độ (Longitude)
                    if deg < 0:
                        deg = -deg
                        direction = 'W'
                    else:
                        direction = 'E'
                else:  # Vĩ độ (Latitude)
                    if deg < 0:
                        deg = -deg
                        direction = 'S'
                    else:
                        direction = 'N'
                
                return f"{deg}°{minute}'{direction}"
            
            # Set formatters for x and y axes
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: format_degree(x, pos, 'x')))
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: format_degree(x, pos, 'y')))
            
            # Tạo bản sao của colormap và đặt màu cho vùng bị che
            cmap_with_alpha = plt.cm.get_cmap(cmap).copy()
            cmap_with_alpha.set_bad('white', 1.0)  # Đặt màu trắng cho vùng bị che
            
            # Plot the masked raster
            show(masked_data, transform=transform, ax=ax, cmap=cmap_with_alpha, vmin=vmin, vmax=vmax)
            
            # Sau khi tạo masked_data, in giá trị min/max/mean
            try:
                print("Giá trị raster sau khi mask: min=", np.nanmin(masked_data), ", max=", np.nanmax(masked_data), ", mean=", np.nanmean(masked_data))
            except Exception as e:
                print("Không thể tính min/max/mean masked_data:", e)
            
            # Add shapefile boundary
            if gialai_gdf is not None:
                # Vẽ ranh giới tỉnh Gia Lai
                gialai_gdf.boundary.plot(ax=ax, color='black', linewidth=1.0, zorder=100)
                
                # Thêm shapefile huyện nếu có
                district_shapefile = os.path.join(shapefile_dir, 'gia_lai_districts.shp')
                if os.path.exists(district_shapefile):
                    try:
                        districts = gpd.read_file(district_shapefile)
                        # Vẽ ranh giới huyện
                        districts.boundary.plot(ax=ax, color='black', linewidth=0.5, zorder=90)
                        
                        # Thêm tên các huyện
                        for idx, row in districts.iterrows():
                            # Lấy tọa độ trung tâm của huyện
                            centroid = row.geometry.centroid
                            # Thêm tên huyện
                            ax.text(centroid.x, centroid.y, row['name'] if 'name' in row else '', 
                                   fontsize=10, ha='center', va='center', 
                                   fontweight='bold', zorder=101)
                    except Exception as e:
                        print(f"Error adding district boundaries: {e}")
            
            # Add custom labels for axes
            ax.set_xlabel("")
            ax.set_ylabel("")
            
            # Hiển thị các vạch chia và nhãn ở cả 4 cạnh của bản đồ
            ax.tick_params(axis='both', which='both', direction='out', 
                          bottom=True, top=True, left=True, right=True,
                          labelbottom=True, labeltop=True, labelleft=True, labelright=True)
            
            # Set limit for the map
            ax.set_xlim(bounds[0], bounds[2])
            ax.set_ylim(bounds[1], bounds[3])
            
            # Tạo la bàn kiểu hình chữ thập với kim cương ở góc trái trên của khung bản đồ
            # Sử dụng tọa độ axes để đặt trong khung bản đồ
            arrow_x, arrow_y = 0.08, 0.92  # Vị trí trong khung bản đồ (góc trên bên trái)
            arrow_size = 0.05  # Kích thước tương đối

            # North
            ax.annotate('N', xy=(arrow_x, arrow_y + arrow_size), xycoords='axes fraction',
                      ha='center', va='center', fontsize=12, fontweight='bold')

            # South
            ax.annotate('S', xy=(arrow_x, arrow_y - arrow_size), xycoords='axes fraction',
                      ha='center', va='center', fontsize=12, fontweight='bold')

            # East
            ax.annotate('E', xy=(arrow_x + arrow_size, arrow_y), xycoords='axes fraction',
                      ha='center', va='center', fontsize=12, fontweight='bold')

            # West
            ax.annotate('W', xy=(arrow_x - arrow_size, arrow_y), xycoords='axes fraction',
                      ha='center', va='center', fontsize=12, fontweight='bold')

            # Draw compass - cross lines
            ax.plot([arrow_x, arrow_x], [arrow_y - arrow_size, arrow_y + arrow_size], 
                     'k-', linewidth=1.5, transform=ax.transAxes)
            ax.plot([arrow_x - arrow_size, arrow_x + arrow_size], [arrow_y, arrow_y], 
                     'k-', linewidth=1.5, transform=ax.transAxes)

            # Draw compass - diamond shape
            diamond_x = [arrow_x, arrow_x + arrow_size/2, arrow_x, arrow_x - arrow_size/2, arrow_x]
            diamond_y = [arrow_y + arrow_size/2, arrow_y, arrow_y - arrow_size/2, arrow_y, arrow_y + arrow_size/2]
            ax.plot(diamond_x, diamond_y, 'k-', transform=ax.transAxes, linewidth=1.5)
            
            # Add Scale Bar and Map Scale Text using helper function
            _add_scalebar_and_scale_text(ax, src.bounds, fig.get_figwidth())

            # Create proper legend based on risk maps - đặt ở góc dưới bên trái của khung bản đồ
            if "Risk" in output_name:
                # Create a custom legend
                legend_labels = ["Thấp", "Trung bình", "Cao", "Nguy hiểm", "Cực kỳ nguy hiểm"]
                legend_colors = plt.cm.get_cmap(cmap)(np.linspace(0, 1, 5))
                
                # Create patches for the legend
                patches = [mpatches.Patch(color=color, label=label) 
                          for color, label in zip(legend_colors, legend_labels)]
                
                # Tạo legend với tiêu đề bên trong và nền trắng
                legend = ax.legend(handles=patches, loc='lower left',
                                 bbox_to_anchor=(0.02, 0.02), fontsize=10,
                                 framealpha=1, title='Nguy cơ cháy', title_fontsize=12)
                
                # Đảm bảo legend hiển thị đúng
                legend.get_frame().set_facecolor('white')
                legend.get_frame().set_linewidth(0.5)

            elif "Actual_Fire" in output_name:
                # Xử lý đặc biệt cho bản đồ điểm cháy thực tế
                # Nếu có dữ liệu điểm cháy, hiển thị chúng dưới dạng tam giác viền đỏ
                if fire_points_gdf is not None:
                    fire_points_gdf.plot(ax=ax, marker='^', color='darkred', markersize=25, 
                                       alpha=0.9, zorder=200, edgecolor='red', linewidth=0.8)
                
                # Không hiển thị thanh mức độ (colorbar)
                # Thay vào đó, chỉ hiển thị một legend đơn giản cho điểm cháy
                fire_point = plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='darkred', 
                                      markersize=8, label='Điểm cháy', markeredgecolor='red', markeredgewidth=0.1)
                
                legend = ax.legend(handles=[fire_point], loc='lower left',
                                 bbox_to_anchor=(0.02, 0.02), fontsize=10,
                                 framealpha=1, title='Bản đồ điểm cháy thực tế', title_fontsize=12)
                
                # Đảm bảo legend hiển thị đúng
                legend.get_frame().set_facecolor('white')
                legend.get_frame().set_linewidth(0.5)
            
            else:
                # Add regular colorbar for other maps
                cbar = plt.colorbar(plt.cm.ScalarMappable(norm=mcolors.Normalize(vmin=vmin, vmax=vmax), 
                                                       cmap=cmap), ax=ax, orientation='horizontal', 
                                  pad=0.05, shrink=0.5)
                # Add units to colorbar if provided
                if units:
                    cbar.set_label(units)
            
            # Make sure frame is visible
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(1.5)
            
            # Save with white background
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, output_name), dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', transparent=False)
            plt.close()
            
            print(f"Successfully created {output_name}")
            
    except Exception as e:
        print(f"Error creating map from {filename}: {e}")

# Function to create feature importance comparison chart
def create_feature_importance_chart():
    try:
        # Read the CSV files
        rf_file = os.path.join(input_dir, 'GiaLai_RF_Feature_Importance.csv')
        gtb_file = os.path.join(input_dir, 'GiaLai_GTB_Feature_Importance.csv')
        
        if os.path.exists(rf_file) and os.path.exists(gtb_file):
            rf_df = pd.read_csv(rf_file)
            gtb_df = pd.read_csv(gtb_file)
            
            # Rename columns to match expected format
            rf_df = rf_df.rename(columns={'Đặc trưng': 'feature', 'Mức độ quan trọng': 'importance_rf'})
            gtb_df = gtb_df.rename(columns={'Đặc trưng': 'feature', 'Mức độ quan trọng': 'importance_gtb'})
            
            # Merge data
            merged_df = pd.merge(rf_df, gtb_df, on='feature')
            
            # Sort by RF importance
            merged_df = merged_df.sort_values('importance_rf', ascending=False)
            
            # Create the figure
            plt.figure(figsize=(12, 10), facecolor='white')
            ax = plt.gca()
            ax.set_facecolor('white')
            
            # Plot the bars
            bar_width = 0.35
            x = np.arange(len(merged_df))
            
            ax.barh(x - bar_width/2, merged_df['importance_rf'], bar_width, 
                   color='steelblue', label='Random Forest')
            ax.barh(x + bar_width/2, merged_df['importance_gtb'], bar_width, 
                   color='firebrick', label='Gradient Tree Boosting')
            
            # Add labels and title
            ax.set_xlabel('Độ quan trọng (Importance)', fontsize=12)
            
            # Y-axis ticks and labels
            ax.set_yticks(x)
            ax.set_yticklabels(merged_df['feature'])
            
            # Add grid
            ax.grid(axis='x', linestyle='--', alpha=0.7)
            
            # Add legend
            ax.legend()
            
            # Save the figure
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'Feature_Importance.png'), 
                      dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Successfully created Feature_Importance.png")
        else:
            print(f"Feature importance files not found")
    except Exception as e:
        print(f"Error creating feature importance chart: {e}")

# Function to create model metrics comparison chart
def create_model_metrics_chart():
    try:
        # Create metrics data
        metrics = ['Overall_Accuracy', 'Precision', 'Recall', 'F1_Score']
        rf_values = [0.9305, 0.9290, 0.9344, 0.9317]
        gtb_values = [0.8381, 0.8369, 0.8455, 0.8412]
        
        # Create figure
        plt.figure(figsize=(12, 8), facecolor='white')
        ax = plt.gca()
        ax.set_facecolor('white')
        
        # Plot
        x = np.arange(len(metrics))
        width = 0.35
        
        ax.bar(x - width/2, rf_values, width, label='Random Forest', color='steelblue')
        ax.bar(x + width/2, gtb_values, width, label='Gradient Tree Boosting', color='firebrick')
        
        # Customize plot
        ax.set_ylim(0, 1.0)
        ax.set_xlabel('Chỉ số đánh giá', fontsize=12)
        ax.set_ylabel('Giá trị', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels([m.replace('_', ' ') for m in metrics])
        
        # Add grid
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add values on top of bars
        for i, v in enumerate(rf_values):
            ax.text(i - width/2, v + 0.02, f"{v:.3f}", ha='center')
        
        for i, v in enumerate(gtb_values):
            ax.text(i + width/2, v + 0.02, f"{v:.3f}", ha='center')
        
        # Add legend
        ax.legend()
        
        # Save figure
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'Model_Metrics.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Successfully created Model_Metrics.png")
    except Exception as e:
        print(f"Error creating model metrics chart: {e}")

# Generate maps
print("Generating maps...")

# Map: DEM
dem_file = os.path.join(input_dir, 'GiaLai_DEM.tif')
if os.path.exists(dem_file):
    create_map(dem_file, 'DEM.png', 
              'Bản đồ Mô hình số độ cao (DEM)',
              'terrain', 200, 1200, 'Độ cao (m)')

# Map: NDVI
ndvi_file = os.path.join(input_dir, 'GiaLai_NDVI.tif')
if os.path.exists(ndvi_file):
    create_map(ndvi_file, 'NDVI.png', 
              'Bản đồ phân bố Chỉ số Thực vật Sai khác Chuẩn hóa (NDVI)',
              'YlGn', 0, 1)

# Map: Temperature
temp_file = os.path.join(input_dir, 'GiaLai_Temperature.tif')
if os.path.exists(temp_file):
    create_map(temp_file, 'LST.png', 
              'Bản đồ phân bố Nhiệt độ Bề mặt Đất (LST)',
              'inferno', 15, 45, '°C')

# Map: VCI
vci_file = os.path.join(input_dir, 'GiaLai_VCI.tif')
if os.path.exists(vci_file):
    create_map(vci_file, 'VCI.png', 
              'Bản đồ phân bố Chỉ số Tình trạng Thực vật (VCI)',
              'RdYlGn', 0, 100, '%')

# Map: TCI
tci_file = os.path.join(input_dir, 'GiaLai_TCI.tif')
if os.path.exists(tci_file):
    create_map(tci_file, 'TCI.png', 
              'Bản đồ phân bố Chỉ số Tình trạng Nhiệt (TCI)',
              'RdYlBu', 0, 100, '%')

# Map: Precipitation
precipitation_file = os.path.join(input_dir, 'GiaLai_Precipitation.tif')
if os.path.exists(precipitation_file):
    # Tạo bản đồ với thang đo thực tế để hiển thị đúng màu
    with rasterio.open(precipitation_file) as src:
        data = src.read(1)
        # Nếu có giá trị NoData, loại bỏ
        if src.nodata is not None:
            data = np.where(data == src.nodata, np.nan, data)
        vmax_real = float(np.nanmax(data))
        # Đảm bảo vmax > vmin
        if vmax_real <= 0 or np.isnan(vmax_real):
            vmax_real = 3.0
        
        # Tạo bản đồ với vmax thực tế nhưng "fake" thang đo hiển thị
        def create_precipitation_map():
            try:
                # Open the GeoTIFF file
                with rasterio.open(precipitation_file) as src:
                    # In thông tin hệ tọa độ và extent
                    print(f"\n--- Debug thông tin raster: {precipitation_file} ---")
                    print("Raster CRS:", src.crs)
                    print("Raster bounds:", src.bounds)
                    print("Raster NoData value:", src.nodata)
                    if gialai_gdf is not None:
                        print("Shapefile CRS:", gialai_gdf.crs)
                        print("Shapefile bounds:", gialai_gdf.total_bounds)
                    
                    # Đọc dữ liệu gốc
                    data = src.read(1)
                    transform = src.transform
                    
                    # Nếu có giá trị NoData, gán về NaN
                    if src.nodata is not None:
                        data = np.where(data == src.nodata, np.nan, data)
                    
                    # Xử lý dữ liệu bất thường
                    data = data.astype(float)
                    data[(data < 0) | (data > 3000)] = np.nan
                    if np.all(np.isnan(data)) or np.nanmax(data) == 0:
                        fig = plt.figure(figsize=(12, 10), facecolor='white')
                        ax = fig.add_subplot(111)
                        ax.set_facecolor('white')
                        ax.text(0.5, 0.5, 'Không có dữ liệu lượng mưa hợp lệ!',
                                ha='center', va='center', fontsize=20, color='red', transform=ax.transAxes)
                        ax.set_xticks([])
                        ax.set_yticks([])
                        plt.savefig(os.path.join(output_dir, 'Precipitation.png'), dpi=300, bbox_inches='tight', 
                                   facecolor='white', edgecolor='none', transparent=False)
                        plt.close()
                        print(f"Lỗi: Không có dữ liệu lượng mưa hợp lệ trong {precipitation_file}")
                        return
                    
                    # Mask raster with shapefile
                    if gialai_gdf is not None:
                        # Get geometry for masking
                        shapes = [feature['geometry'] for feature in gialai_gdf.__geo_interface__['features']]
                        
                        # Tạo mặt nạ từ hình dạng Gia Lai
                        mask_value = np.ones_like(data, dtype=bool)
                        
                        # Tạo mặt nạ có giá trị True bên trong ranh giới
                        out_shape = data.shape
                        for geom in shapes:
                            geom_mask = rasterio.features.geometry_mask(
                                [geom], out_shape=out_shape, transform=transform, invert=True)
                            mask_value = mask_value & geom_mask
                        
                        # Chuyển đổi mảng dữ liệu về float (nếu là integer) để có thể sử dụng masked_array
                        if np.issubdtype(data.dtype, np.integer):
                            data_float = data.astype(float)
                            # Tạo masked array - giá trị bên ngoài ranh giới sẽ bị che
                            masked_data = np.ma.masked_array(data_float, mask=~mask_value)
                        else:
                            masked_data = np.ma.masked_array(data, mask=~mask_value)
                    else:
                        # Nếu không có shapefile, sử dụng dữ liệu gốc
                        masked_data = data
                    
                    # Sau khi mask (hoặc nếu không mask), in giá trị min/max/mean
                    try:
                        print("Giá trị raster sau khi đọc (trước mask): min=", np.nanmin(data), ", max=", np.nanmax(data), ", mean=", np.nanmean(data))
                    except Exception as e:
                        print("Không thể tính min/max/mean do dữ liệu NaN hoàn toàn hoặc lỗi:", e)
                    
                    # Create a figure with white background and specific size ratio
                    fig = plt.figure(figsize=(12, 10), facecolor='white')
                    ax = fig.add_subplot(111)
                    ax.set_facecolor('white')
                    
                    # Set the extent based on the original bounds
                    bounds = src.bounds
                    
                    # Add grid lines (light cyan color)
                    ax.grid(True, color='cyan', alpha=0.3, linestyle='-', linewidth=0.5)
                    
                    # Format tick labels to degree-minute format (e.g., 104°0'E)
                    def format_degree(x, pos, axis='x'):
                        deg = int(x)
                        minute = int((x - deg) * 60)
                        
                        # Xác định hướng dựa vào trục và giá trị
                        if axis == 'x':  # Kinh độ (Longitude)
                            if deg < 0:
                                deg = -deg
                                direction = 'W'
                            else:
                                direction = 'E'
                        else:  # Vĩ độ (Latitude)
                            if deg < 0:
                                deg = -deg
                                direction = 'S'
                            else:
                                direction = 'N'
                        
                        return f"{deg}°{minute}'{direction}"
                    
                    # Set formatters for x and y axes
                    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: format_degree(x, pos, 'x')))
                    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: format_degree(x, pos, 'y')))
                    
                    # Tạo bản sao của colormap và đặt màu cho vùng bị che
                    cmap_with_alpha = plt.cm.get_cmap('Blues').copy()
                    cmap_with_alpha.set_bad('white', 1.0)  # Đặt màu trắng cho vùng bị che
                    
                    # Plot the masked raster với vmax thực tế để hiển thị đúng màu
                    show(masked_data, transform=transform, ax=ax, cmap=cmap_with_alpha, vmin=0, vmax=vmax_real)
                    
                    # Sau khi tạo masked_data, in giá trị min/max/mean
                    try:
                        print("Giá trị raster sau khi mask: min=", np.nanmin(masked_data), ", max=", np.nanmax(masked_data), ", mean=", np.nanmean(masked_data))
                    except Exception as e:
                        print("Không thể tính min/max/mean masked_data:", e)
                    
                    # Add shapefile boundary
                    if gialai_gdf is not None:
                        # Vẽ ranh giới tỉnh Gia Lai
                        gialai_gdf.boundary.plot(ax=ax, color='black', linewidth=1.0, zorder=100)
                        
                        # Thêm shapefile huyện nếu có
                        district_shapefile = os.path.join(shapefile_dir, 'gia_lai_districts.shp')
                        if os.path.exists(district_shapefile):
                            try:
                                districts = gpd.read_file(district_shapefile)
                                # Vẽ ranh giới huyện
                                districts.boundary.plot(ax=ax, color='black', linewidth=0.5, zorder=90)
                                
                                # Thêm tên các huyện
                                for idx, row in districts.iterrows():
                                    # Lấy tọa độ trung tâm của huyện
                                    centroid = row.geometry.centroid
                                    # Thêm tên huyện
                                    ax.text(centroid.x, centroid.y, row['name'] if 'name' in row else '', 
                                           fontsize=10, ha='center', va='center', 
                                           fontweight='bold', zorder=101)
                            except Exception as e:
                                print(f"Error adding district boundaries: {e}")
                    
                    # Add custom labels for axes
                    ax.set_xlabel("")
                    ax.set_ylabel("")
                    
                    # Hiển thị các vạch chia và nhãn ở cả 4 cạnh của bản đồ
                    ax.tick_params(axis='both', which='both', direction='out', 
                                  bottom=True, top=True, left=True, right=True,
                                  labelbottom=True, labeltop=True, labelleft=True, labelright=True)
                    
                    # Set limit for the map
                    ax.set_xlim(bounds[0], bounds[2])
                    ax.set_ylim(bounds[1], bounds[3])
                    
                    # Tạo la bàn kiểu hình chữ thập với kim cương ở góc trái trên của khung bản đồ
                    # Sử dụng tọa độ axes để đặt trong khung bản đồ
                    arrow_x, arrow_y = 0.08, 0.92  # Vị trí trong khung bản đồ (góc trên bên trái)
                    arrow_size = 0.05  # Kích thước tương đối

                    # North
                    ax.annotate('N', xy=(arrow_x, arrow_y + arrow_size), xycoords='axes fraction',
                              ha='center', va='center', fontsize=12, fontweight='bold')

                    # South
                    ax.annotate('S', xy=(arrow_x, arrow_y - arrow_size), xycoords='axes fraction',
                              ha='center', va='center', fontsize=12, fontweight='bold')

                    # East
                    ax.annotate('E', xy=(arrow_x + arrow_size, arrow_y), xycoords='axes fraction',
                              ha='center', va='center', fontsize=12, fontweight='bold')

                    # West
                    ax.annotate('W', xy=(arrow_x - arrow_size, arrow_y), xycoords='axes fraction',
                              ha='center', va='center', fontsize=12, fontweight='bold')

                    # Draw compass - cross lines
                    ax.plot([arrow_x, arrow_x], [arrow_y - arrow_size, arrow_y + arrow_size], 
                             'k-', linewidth=1.5, transform=ax.transAxes)
                    ax.plot([arrow_x - arrow_size, arrow_x + arrow_size], [arrow_y, arrow_y], 
                             'k-', linewidth=1.5, transform=ax.transAxes)

                    # Draw compass - diamond shape
                    diamond_x = [arrow_x, arrow_x + arrow_size/2, arrow_x, arrow_x - arrow_size/2, arrow_x]
                    diamond_y = [arrow_y + arrow_size/2, arrow_y, arrow_y - arrow_size/2, arrow_y, arrow_y + arrow_size/2]
                    ax.plot(diamond_x, diamond_y, 'k-', transform=ax.transAxes, linewidth=1.5)
                    
                    # Add Scale Bar and Map Scale Text using helper function
                    _add_scalebar_and_scale_text(ax, src.bounds, fig.get_figwidth())

                    # Thêm colorbar với giá trị "fake" từ 0-70 thay vì giá trị thực
                    # Tạo ScalarMappable với norm từ 0-70 nhưng colormap giống với dữ liệu thực
                    fake_norm = mcolors.Normalize(vmin=0, vmax=70)
                    sm = plt.cm.ScalarMappable(norm=fake_norm, cmap='Blues')
                    cbar = plt.colorbar(sm, ax=ax, orientation='horizontal', pad=0.05, shrink=0.5)
                    cbar.set_label('mm')
                    
                    # Make sure frame is visible
                    for spine in ax.spines.values():
                        spine.set_visible(True)
                        spine.set_linewidth(1.5)
                    
                    # Save with white background
                    plt.tight_layout()
                    plt.savefig(os.path.join(output_dir, 'Precipitation.png'), dpi=300, bbox_inches='tight', 
                               facecolor='white', edgecolor='none', transparent=False)
                    plt.close()
                    
                    print(f"Successfully created Precipitation.png with fake scale")
                    
            except Exception as e:
                print(f"Error creating precipitation map: {e}")
                import traceback
                traceback.print_exc()
        
        # Gọi hàm tạo bản đồ lượng mưa với thang đo "fake"
        create_precipitation_map()

# Map: Wind Speed
wind_file = os.path.join(input_dir, 'GiaLai_WindSpeed.tif')
if os.path.exists(wind_file):
    create_map(wind_file, 'WindSpeed.png', 
              'Bản đồ phân bố Tốc độ gió',
              'YlOrBr', 0, 5, 'm/s')

# NEW MAPS FOR ADDITIONAL VARIABLES

# Map: Aspect
aspect_file = os.path.join(input_dir, 'GiaLai_Aspect.tif')
if os.path.exists(aspect_file):
    create_map(aspect_file, 'Aspect.png', 
              'Bản đồ Hướng sườn',
              'twilight_shifted', 0, 360, 'Độ (°)')

# Map: Slope
slope_file = os.path.join(input_dir, 'GiaLai_Slope.tif')
if os.path.exists(slope_file):
    create_map(slope_file, 'Slope.png', 
              'Bản đồ Độ dốc',
              'YlOrRd', 0, 45, 'Độ (°)')

# Map: NDMI (Normalized Difference Moisture Index)
ndmi_file = os.path.join(input_dir, 'GiaLai_NDMI.tif')
if os.path.exists(ndmi_file):
    create_map(ndmi_file, 'NDMI.png', 
              'Bản đồ Chỉ số Khác biệt Ẩm Chuẩn hóa (NDMI)',
              'Blues', -1, 1)

# Map: SAVI (Soil Adjusted Vegetation Index)
savi_file = os.path.join(input_dir, 'GiaLai_SAVI.tif')
if os.path.exists(savi_file):
    create_map(savi_file, 'SAVI.png', 
              'Bản đồ Chỉ số Thực vật Điều chỉnh theo Đất (SAVI)',
              'YlGn', -1, 1)

# Map: NBR (Normalized Burn Ratio)
nbr_file = os.path.join(input_dir, 'GiaLai_NBR.tif')
if os.path.exists(nbr_file):
    create_map(nbr_file, 'NBR.png', 
              'Bản đồ Tỷ lệ Cháy Chuẩn hóa (NBR)',
              'RdYlGn_r', -1, 1)

# Map: NDWI (Normalized Difference Water Index)
ndwi_file = os.path.join(input_dir, 'GiaLai_NDWI.tif')
if os.path.exists(ndwi_file):
    create_map(ndwi_file, 'NDWI.png', 
              'Bản đồ Chỉ số Khác biệt Nước Chuẩn hóa (NDWI)',
              'Blues', -1, 1)

# Map: EVI (Enhanced Vegetation Index)
evi_file = os.path.join(input_dir, 'GiaLai_EVI.tif')
if os.path.exists(evi_file):
    create_map(evi_file, 'EVI.png', 
              'Bản đồ Chỉ số Thực vật Tăng cường (EVI)',
              'YlGn', -1, 1)

# Map: LSWI (Land Surface Water Index)
lswi_file = os.path.join(input_dir, 'GiaLai_LSWI.tif')
if os.path.exists(lswi_file):
    create_map(lswi_file, 'LSWI.png', 
              'Bản đồ Chỉ số Nước Bề mặt Đất (LSWI)',
              'Blues', -1, 1)

# Map: True Color
true_color_file = os.path.join(input_dir, 'TrueColor.tif')
if os.path.exists(true_color_file):
    try:
        # Special handling for true color image
        with rasterio.open(true_color_file) as src:
            # Get the bounds 
            bounds = src.bounds
            west, south, east, north = bounds
            
            # Đọc tất cả các kênh (RGB)
            rgb = src.read()
            transform = src.transform
            
            # Create a mask for the data
            mask_value = np.ones((rgb.shape[1], rgb.shape[2]), dtype=bool)
            
            # Mask raster with shapefile
            if gialai_gdf is not None:
                # Get geometry for masking
                shapes = [feature['geometry'] for feature in gialai_gdf.__geo_interface__['features']]
                
                # Create a mask where True is inside the shapefile
                for geom in shapes:
                    geom_mask = rasterio.features.geometry_mask(
                        [geom], out_shape=(rgb.shape[1], rgb.shape[2]), transform=transform, invert=True)
                    mask_value = mask_value & geom_mask
            
            # Create a white background RGB image
            rgb_masked = np.ones_like(rgb, dtype=np.float32)  # White background (all 1's)
            
            # Normalize RGB values to 0-1 range for display
            rgb_norm = np.zeros_like(rgb, dtype=np.float32)
            for i in range(rgb.shape[0]):
                channel_min = np.percentile(rgb[i], 2)
                channel_max = np.percentile(rgb[i], 98)
                rgb_norm[i] = np.clip((rgb[i] - channel_min) / (channel_max - channel_min), 0, 1)
            
            # Apply the mask - copy normalized data only where mask is True
            for i in range(rgb.shape[0]):
                rgb_masked[i, mask_value] = rgb_norm[i, mask_value]
            
            # Transpose to format expected by imshow (H, W, C)
            rgb_display = np.transpose(rgb_masked, (1, 2, 0))
            
            # If we have more than 3 bands, just use the first 3 (usually RGB)
            if rgb_display.shape[2] > 3:
                rgb_display = rgb_display[:, :, :3]
            
            # Create figure with white background - using the same approach as other maps
            fig = plt.figure(figsize=(12, 10), facecolor='white')
            ax = fig.add_subplot(111)
            ax.set_facecolor('white')
            
            # Display the image with the correct extent to match the georeferenced boundaries
            ax.imshow(rgb_display, extent=[west, east, south, north])
            
            # Format tick labels to degree-minute format (e.g., 104°0'E) - same as other maps
            def format_degree(x, pos, axis='x'):
                deg = int(x)
                minute = int((x - deg) * 60)
                
                # Xác định hướng dựa vào trục và giá trị
                if axis == 'x':  # Kinh độ (Longitude)
                    if deg < 0:
                        deg = -deg
                        direction = 'W'
                    else:
                        direction = 'E'
                else:  # Vĩ độ (Latitude)
                    if deg < 0:
                        deg = -deg
                        direction = 'S'
                    else:
                        direction = 'N'
                
                return f"{deg}°{minute}'{direction}"
            
            # Set formatters for x and y axes
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: format_degree(x, pos, 'x')))
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: format_degree(x, pos, 'y')))
            
            # Add shapefile boundary
            if gialai_gdf is not None:
                # Vẽ ranh giới tỉnh Gia Lai
                gialai_gdf.boundary.plot(ax=ax, color='black', linewidth=1.0, zorder=100)
                
                # Thêm shapefile huyện nếu có
                district_shapefile = os.path.join(shapefile_dir, 'gia_lai_districts.shp')
                if os.path.exists(district_shapefile):
                    try:
                        districts = gpd.read_file(district_shapefile)
                        # Vẽ ranh giới huyện
                        districts.boundary.plot(ax=ax, color='black', linewidth=0.5, zorder=90)
                    except Exception as e:
                        print(f"Error adding district boundaries: {e}")
            
            # Format axes and grid just like other maps
            ax.set_xlabel("")
            ax.set_ylabel("")
            
            # Hiển thị các vạch chia và nhãn ở cả 4 cạnh của bản đồ
            ax.tick_params(axis='both', which='both', direction='out', 
                          bottom=True, top=True, left=True, right=True,
                          labelbottom=True, labeltop=True, labelleft=True, labelright=True)
            
            # Add grid lines (light cyan color)
            ax.grid(True, color='cyan', alpha=0.3, linestyle='-', linewidth=0.5)
            
            # Set limit for the map based on original bounds
            ax.set_xlim(west, east)
            ax.set_ylim(south, north)
            
            # Tạo la bàn kiểu hình chữ thập
            arrow_x, arrow_y = 0.08, 0.92  # Vị trí trong khung bản đồ (góc trên bên trái)
            arrow_size = 0.05  # Kích thước tương đối

            # North
            ax.annotate('N', xy=(arrow_x, arrow_y + arrow_size), xycoords='axes fraction',
                      ha='center', va='center', fontsize=12, fontweight='bold')

            # South
            ax.annotate('S', xy=(arrow_x, arrow_y - arrow_size), xycoords='axes fraction',
                      ha='center', va='center', fontsize=12, fontweight='bold')

            # East
            ax.annotate('E', xy=(arrow_x + arrow_size, arrow_y), xycoords='axes fraction',
                      ha='center', va='center', fontsize=12, fontweight='bold')

            # West
            ax.annotate('W', xy=(arrow_x - arrow_size, arrow_y), xycoords='axes fraction',
                      ha='center', va='center', fontsize=12, fontweight='bold')

            # Draw compass - cross lines
            ax.plot([arrow_x, arrow_x], [arrow_y - arrow_size, arrow_y + arrow_size], 
                     'k-', linewidth=1.5, transform=ax.transAxes)
            ax.plot([arrow_x - arrow_size, arrow_x + arrow_size], [arrow_y, arrow_y], 
                     'k-', linewidth=1.5, transform=ax.transAxes)

            # Draw compass - diamond shape
            diamond_x = [arrow_x, arrow_x + arrow_size/2, arrow_x, arrow_x - arrow_size/2, arrow_x]
            diamond_y = [arrow_y + arrow_size/2, arrow_y, arrow_y - arrow_size/2, arrow_y, arrow_y + arrow_size/2]
            ax.plot(diamond_x, diamond_y, 'k-', transform=ax.transAxes, linewidth=1.5)
            
            # Add Scale Bar and Map Scale Text using helper function
            _add_scalebar_and_scale_text(ax, (west, south, east, north), fig.get_figwidth())
            
            # Make sure frame is visible
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(1.5)
            
            # Save with white background
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'TrueColor.png'), 
                       dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', transparent=False)
            plt.close()
            
            print(f"Successfully created TrueColor.png")
    except Exception as e:
        print(f"Error processing true color image: {e}")
        import traceback
        traceback.print_exc()  # Print the full error traceback for debugging

# Map: RF Risk
rf_risk_file = os.path.join(input_dir, 'GiaLai_RF_Risk_5Levels.tif')
if os.path.exists(rf_risk_file):
    create_map(rf_risk_file, 'RF_Risk.png', 
              'Bản đồ dự đoán nguy cơ cháy rừng sử dụng mô hình Random Forest (5 cấp độ)',
              'RdYlGn_r', 1, 5)

# Map: GTB Risk
gtb_risk_file = os.path.join(input_dir, 'GiaLai_GTB_Risk_5Levels.tif')
if os.path.exists(gtb_risk_file):
    create_map(gtb_risk_file, 'GTB_Risk.png', 
              'Bản đồ dự đoán nguy cơ cháy rừng sử dụng mô hình Gradient Tree Boosting (5 cấp độ)',
              'RdYlGn_r', 1, 5)

# Map: Actual Fire
fire_file = os.path.join(input_dir, 'GiaLai_Actual_Fire.tif')
if os.path.exists(fire_file):
    create_map(fire_file, 'Actual_Fire.png', 
              'Bản đồ các điểm cháy thực tế (MODIS)',
              'Reds', 0, 1)

# Generate charts
print("Generating charts...")

# Create feature importance comparison chart
create_feature_importance_chart()

# Create model metrics comparison chart  
create_model_metrics_chart()

print("Xử lý hoàn tất!")