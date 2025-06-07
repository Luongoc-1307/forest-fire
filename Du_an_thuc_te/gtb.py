import rasterio
import numpy as np

pixel_area_ha = 0.09 # Ví dụ: pixel 30m x 30m = 0.09 ha
total_study_area_ha = 1556000 # Tổng diện tích tỉnh Gia Lai

with rasterio.open('/Users/ninhhaidang/Library/CloudStorage/GoogleDrive-ninhhailongg@gmail.com/My Drive/Cac_mon_hoc/Nam4_Ky2/Cac_van_de_hien_dai_trong_Vien_tham_va_GIS/gee-exported/GiaLai_RF_Risk_5Levels.tif') as src:
    image = src.read(1) # Đọc band đầu tiên

    # Đếm số pixel cho mỗi cấp độ (giả sử cấp độ là 1, 2, 3, 4, 5)
    unique_values, counts = np.unique(image, return_counts=True)
    pixel_counts = dict(zip(unique_values, counts))

    print("Thống kê diện tích (GTB Model):")
    for level in range(1, 6): # Giả sử có 5 cấp độ
        if level in pixel_counts:
            area_ha = pixel_counts[level] * pixel_area_ha
            percentage = (area_ha / total_study_area_ha) * 100
            print(f"Cấp độ {level}: {area_ha:.3f} ha ({percentage:.1f}%)")
        else:
            print(f"Cấp độ {level}: 0 ha (0.0%)")
