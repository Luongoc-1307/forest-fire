import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

# Thiết lập đường dẫn đến thư mục chứa dữ liệu (điều chỉnh theo cấu trúc thư mục của người dùng)
csv_dir = '/Users/ninhhaidang/Library/CloudStorage/GoogleDrive-ninhhailongg@gmail.com/My Drive/Cac_mon_hoc/Nam4_Ky2/Cac_van_de_hien_dai_trong_Vien_tham_va_GIS/gee-exported'
training_data_path = f'{csv_dir}/GiaLai_Training_Data_For_Feature_Importance.csv'
feature_names_path = f'{csv_dir}/GiaLai_Feature_Names.csv'
output_dir = csv_dir  # Sử dụng cùng thư mục cho đầu ra phân tích

# Đọc và kiểm tra dữ liệu
print("Đang đọc dữ liệu từ CSV...")
try:
    data = pd.read_csv(training_data_path)
    feature_names_df = pd.read_csv(feature_names_path)
    feature_names = feature_names_df['feature_name'].tolist()
    
    print(f"Tổng số mẫu: {data.shape[0]}")
    print(f"Số đặc trưng: {len(feature_names)}")
    
    # Kiểm tra sự cân bằng của dữ liệu giữa các lớp
    class_counts = data['Fire_Label'].value_counts()
    print("\nPhân phối nhãn:")
    print(f"Không cháy (0): {class_counts.get(0, 0)} mẫu ({class_counts.get(0, 0)/data.shape[0]*100:.2f}%)")
    print(f"Cháy (1): {class_counts.get(1, 0)} mẫu ({class_counts.get(1, 0)/data.shape[0]*100:.2f}%)")
    
except Exception as e:
    print(f"Lỗi khi đọc dữ liệu: {e}")
    print("Vui lòng kiểm tra lại đường dẫn đến các tệp CSV!")
    exit(1)

# Chuẩn bị dữ liệu cho huấn luyện mô hình
print("\nChuẩn bị dữ liệu...")
X = data[feature_names]  # Biến độc lập (đặc trưng)
y = data['Fire_Label']   # Biến phụ thuộc (nhãn)

# Thiết lập tham số mô hình (tương đương với cấu hình trong mã GEE)
rf_params = {
    'n_estimators': 100,       # Số lượng cây quyết định
    'min_samples_leaf': 5,     # Số mẫu tối thiểu trong nút lá
    'max_features': 'sqrt',    # Tương đương với bagFraction
    'random_state': 42         # Giá trị seed để đảm bảo tính tái lập
}

gtb_params = {
    'n_estimators': 100,      # Số lượng cây quyết định
    'learning_rate': 0.05,    # Tốc độ học, tương đương với shrinkage
    'subsample': 0.7,         # Tỷ lệ lấy mẫu dữ liệu
    'max_depth': 3,           # Độ sâu tối đa của cây, tương đương với maxNodes ~10
    'random_state': 42        # Giá trị seed để đảm bảo tính tái lập
}

# Huấn luyện mô hình Random Forest
print("\nHuấn luyện mô hình Random Forest...")
rf_model = RandomForestClassifier(**rf_params)
rf_model.fit(X, y)

# Huấn luyện mô hình Gradient Boosting
print("Huấn luyện mô hình Gradient Boosting...")
gb_model = GradientBoostingClassifier(**gtb_params)
gb_model.fit(X, y)

# Đánh giá mô hình với cross-validation (5-fold)
print("\nĐánh giá mô hình với phương pháp 5-fold cross-validation...")
rf_cv_scores = cross_val_score(rf_model, X, y, cv=5)
gb_cv_scores = cross_val_score(gb_model, X, y, cv=5)

print(f"Random Forest - Độ chính xác cross-validation trung bình: {rf_cv_scores.mean():.4f} ± {rf_cv_scores.std():.4f}")
print(f"Gradient Boosting - Độ chính xác cross-validation trung bình: {gb_cv_scores.mean():.4f} ± {gb_cv_scores.std():.4f}")

# Dự đoán trên tập dữ liệu
rf_preds = rf_model.predict(X)
gb_preds = gb_model.predict(X)

# Tính toán các chỉ số đánh giá hiệu suất mô hình
print("\nCác chỉ số đánh giá hiệu suất trên tập dữ liệu:")
print("\nRandom Forest:")
print(f"Độ chính xác (Accuracy): {accuracy_score(y, rf_preds):.4f}")
print(f"Độ chính xác dương tính (Precision): {precision_score(y, rf_preds, zero_division=0):.4f}")
print(f"Độ nhạy (Recall): {recall_score(y, rf_preds, zero_division=0):.4f}")
print(f"Điểm F1 (F1-score): {f1_score(y, rf_preds, zero_division=0):.4f}")

print("\nGradient Boosting:")
print(f"Độ chính xác (Accuracy): {accuracy_score(y, gb_preds):.4f}")
print(f"Độ chính xác dương tính (Precision): {precision_score(y, gb_preds, zero_division=0):.4f}")
print(f"Độ nhạy (Recall): {recall_score(y, gb_preds, zero_division=0):.4f}")
print(f"Điểm F1 (F1-score): {f1_score(y, gb_preds, zero_division=0):.4f}")

# Phân tích độ quan trọng của đặc trưng (Feature Importance)
rf_importance = pd.DataFrame({
    'Đặc trưng': feature_names,
    'Mức độ quan trọng': rf_model.feature_importances_
})
rf_importance = rf_importance.sort_values('Mức độ quan trọng', ascending=False)

gb_importance = pd.DataFrame({
    'Đặc trưng': feature_names,
    'Mức độ quan trọng': gb_model.feature_importances_
})
gb_importance = gb_importance.sort_values('Mức độ quan trọng', ascending=False)

# Hiển thị kết quả phân tích độ quan trọng đặc trưng
print("\nRandom Forest - Độ quan trọng của đặc trưng:")
print(rf_importance.to_string(index=False))

print("\nGradient Boosting - Độ quan trọng của đặc trưng:")
print(gb_importance.to_string(index=False))

# Lưu kết quả phân tích độ quan trọng đặc trưng ra tệp CSV
rf_importance.to_csv(f'{output_dir}/GiaLai_RF_Feature_Importance.csv', index=False)
gb_importance.to_csv(f'{output_dir}/GiaLai_GTB_Feature_Importance.csv', index=False)
print(f"\nĐã lưu kết quả phân tích độ quan trọng đặc trưng ra tệp {output_dir}/GiaLai_RF_Feature_Importance.csv và {output_dir}/GiaLai_GTB_Feature_Importance.csv")

# Tạo biểu đồ đặc trưng quan trọng cho Random Forest
plt.figure(figsize=(12, 8))
plt.barh(rf_importance['Đặc trưng'][:10], rf_importance['Mức độ quan trọng'][:10])
plt.xlabel('Mức độ quan trọng')
plt.ylabel('Đặc trưng')
plt.title('Top 10 đặc trưng quan trọng nhất - Random Forest')
plt.gca().invert_yaxis()  # Hiển thị từ trên xuống dưới
plt.tight_layout()
plt.savefig(f'{output_dir}/GiaLai_RF_Feature_Importance.png', dpi=300)

# Tạo biểu đồ đặc trưng quan trọng cho Gradient Boosting
plt.figure(figsize=(12, 8))
plt.barh(gb_importance['Đặc trưng'][:10], gb_importance['Mức độ quan trọng'][:10])
plt.xlabel('Mức độ quan trọng')
plt.ylabel('Đặc trưng')
plt.title('Top 10 đặc trưng quan trọng nhất - Gradient Boosting')
plt.gca().invert_yaxis()  # Hiển thị từ trên xuống dưới
plt.tight_layout()
plt.savefig(f'{output_dir}/GiaLai_GTB_Feature_Importance.png', dpi=300)

# Tạo biểu đồ ma trận nhầm lẫn cho Random Forest
plt.figure(figsize=(8, 6))
cm_rf = confusion_matrix(y, rf_preds)
sns.heatmap(cm_rf, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Không cháy', 'Cháy'],
            yticklabels=['Không cháy', 'Cháy'])
plt.xlabel('Dự đoán')
plt.ylabel('Thực tế')
plt.title('Ma trận nhầm lẫn - Random Forest')
plt.tight_layout()
plt.savefig(f'{output_dir}/GiaLai_RF_Confusion_Matrix.png', dpi=300)

# Tạo biểu đồ ma trận nhầm lẫn cho Gradient Boosting
plt.figure(figsize=(8, 6))
cm_gb = confusion_matrix(y, gb_preds)
sns.heatmap(cm_gb, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Không cháy', 'Cháy'],
            yticklabels=['Không cháy', 'Cháy'])
plt.xlabel('Dự đoán')
plt.ylabel('Thực tế')
plt.title('Ma trận nhầm lẫn - Gradient Boosting')
plt.tight_layout()
plt.savefig(f'{output_dir}/GiaLai_GTB_Confusion_Matrix.png', dpi=300)

# Tạo biểu đồ so sánh độ quan trọng đặc trưng giữa hai mô hình
plt.figure(figsize=(14, 10))

# Xác định top 10 đặc trưng quan trọng nhất từ cả hai mô hình
top_features = list(set(rf_importance['Đặc trưng'][:10].tolist() + gb_importance['Đặc trưng'][:10].tolist()))
top_features = sorted(top_features)

# Tạo DataFrame để so sánh
compare_df = pd.DataFrame({
    'Đặc trưng': top_features
})

# Thêm giá trị độ quan trọng từ cả hai mô hình
for feature in top_features:
    rf_value = rf_importance[rf_importance['Đặc trưng'] == feature]['Mức độ quan trọng'].values[0] if feature in rf_importance['Đặc trưng'].values else 0
    gb_value = gb_importance[gb_importance['Đặc trưng'] == feature]['Mức độ quan trọng'].values[0] if feature in gb_importance['Đặc trưng'].values else 0
    compare_df.loc[compare_df['Đặc trưng'] == feature, 'RF'] = rf_value
    compare_df.loc[compare_df['Đặc trưng'] == feature, 'GTB'] = gb_value

# Tạo biểu đồ so sánh
compare_df = compare_df.sort_values('RF', ascending=False)
x = np.arange(len(compare_df))
width = 0.35

fig, ax = plt.subplots(figsize=(14, 10))
ax.bar(x - width/2, compare_df['RF'], width, label='Random Forest')
ax.bar(x + width/2, compare_df['GTB'], width, label='Gradient Boosting')

ax.set_xlabel('Đặc trưng')
ax.set_ylabel('Mức độ quan trọng')
ax.set_title('So sánh mức độ quan trọng của đặc trưng giữa hai mô hình')
ax.set_xticks(x)
ax.set_xticklabels(compare_df['Đặc trưng'], rotation=45, ha='right')
ax.legend()

plt.tight_layout()
plt.savefig(f'{output_dir}/GiaLai_Feature_Importance_Comparison.png', dpi=300)

# Tạo báo cáo tổng hợp đánh giá mô hình
with open(f'{output_dir}/GiaLai_Model_Comparison_Report.txt', 'w', encoding='utf-8') as f:
    f.write("BÁO CÁO SO SÁNH MÔ HÌNH DỰ ĐOÁN NGUY CƠ CHÁY RỪNG TẠI GIA LAI\n")
    f.write("==========================================================\n\n")
    
    f.write("1. THÔNG TIN DỮ LIỆU\n")
    f.write("-----------------\n")
    f.write(f"Tổng số mẫu: {data.shape[0]}\n")
    f.write(f"Số đặc trưng: {len(feature_names)}\n")
    f.write(f"Phân phối nhãn:\n")
    f.write(f"- Không cháy (0): {class_counts.get(0, 0)} mẫu ({class_counts.get(0, 0)/data.shape[0]*100:.2f}%)\n")
    f.write(f"- Cháy (1): {class_counts.get(1, 0)} mẫu ({class_counts.get(1, 0)/data.shape[0]*100:.2f}%)\n\n")
    
    f.write("2. ĐÁNH GIÁ HIỆU SUẤT MÔ HÌNH\n")
    f.write("--------------------------\n")
    f.write("2.1. Random Forest\n")
    f.write(f"- Độ chính xác (Accuracy): {accuracy_score(y, rf_preds):.4f}\n")
    f.write(f"- Độ chính xác dương tính (Precision): {precision_score(y, rf_preds, zero_division=0):.4f}\n")
    f.write(f"- Độ nhạy (Recall): {recall_score(y, rf_preds, zero_division=0):.4f}\n")
    f.write(f"- Điểm F1 (F1-score): {f1_score(y, rf_preds, zero_division=0):.4f}\n")
    f.write(f"- Cross-validation (5-fold): {rf_cv_scores.mean():.4f} ± {rf_cv_scores.std():.4f}\n\n")
    
    f.write("2.2. Gradient Boosting\n")
    f.write(f"- Độ chính xác (Accuracy): {accuracy_score(y, gb_preds):.4f}\n")
    f.write(f"- Độ chính xác dương tính (Precision): {precision_score(y, gb_preds, zero_division=0):.4f}\n")
    f.write(f"- Độ nhạy (Recall): {recall_score(y, gb_preds, zero_division=0):.4f}\n")
    f.write(f"- Điểm F1 (F1-score): {f1_score(y, gb_preds, zero_division=0):.4f}\n")
    f.write(f"- Cross-validation (5-fold): {gb_cv_scores.mean():.4f} ± {gb_cv_scores.std():.4f}\n\n")
    
    f.write("3. TOP 10 ĐẶC TRƯNG QUAN TRỌNG NHẤT\n")
    f.write("--------------------------------\n")
    f.write("3.1. Random Forest\n")
    for i, row in rf_importance[:10].iterrows():
        f.write(f"- {row['Đặc trưng']}: {row['Mức độ quan trọng']:.4f}\n")
    f.write("\n")
    
    f.write("3.2. Gradient Boosting\n")
    for i, row in gb_importance[:10].iterrows():
        f.write(f"- {row['Đặc trưng']}: {row['Mức độ quan trọng']:.4f}\n")
    f.write("\n")
    
    f.write("4. NHẬN XÉT VÀ SO SÁNH\n")
    f.write("---------------------\n")
    if accuracy_score(y, rf_preds) > accuracy_score(y, gb_preds):
        better_model = "Random Forest"
    elif accuracy_score(y, rf_preds) < accuracy_score(y, gb_preds):
        better_model = "Gradient Boosting"
    else:
        better_model = "Cả hai mô hình"
        
    f.write(f"- Về độ chính xác tổng thể, mô hình {better_model} cho kết quả tốt hơn.\n")
    
    # Xác định các đặc trưng chung trong top 5
    common_top5 = set(rf_importance['Đặc trưng'][:5]) & set(gb_importance['Đặc trưng'][:5])
    if common_top5:
        f.write(f"- Cả hai mô hình đều xác định các đặc trưng sau là quan trọng nhất: {', '.join(common_top5)}.\n")
    
    # Phân tích ma trận nhầm lẫn
    rf_fp = cm_rf[0, 1]  # False Positive - Dự đoán dương tính nhưng thực tế âm tính
    rf_fn = cm_rf[1, 0]  # False Negative - Dự đoán âm tính nhưng thực tế dương tính
    gb_fp = cm_gb[0, 1]  # False Positive
    gb_fn = cm_gb[1, 0]  # False Negative
    
    if rf_fp > gb_fp:
        f.write("- Gradient Boosting có ít trường hợp báo động giả (false positive) hơn.\n")
    elif rf_fp < gb_fp:
        f.write("- Random Forest có ít trường hợp báo động giả (false positive) hơn.\n")
    
    if rf_fn > gb_fn:
        f.write("- Gradient Boosting phát hiện cháy rừng tốt hơn (ít false negative hơn).\n")
    elif rf_fn < gb_fn:
        f.write("- Random Forest phát hiện cháy rừng tốt hơn (ít false negative hơn).\n")
    
    f.write("\n")
    f.write("5. KẾT LUẬN\n")
    f.write("---------\n")
    if rf_cv_scores.mean() > gb_cv_scores.mean():
        f.write("- Dựa trên các chỉ số đánh giá và cross-validation, mô hình Random Forest có vẻ phù hợp hơn cho dự đoán nguy cơ cháy rừng tại Gia Lai.\n")
    elif rf_cv_scores.mean() < gb_cv_scores.mean():
        f.write("- Dựa trên các chỉ số đánh giá và cross-validation, mô hình Gradient Boosting có vẻ phù hợp hơn cho dự đoán nguy cơ cháy rừng tại Gia Lai.\n")
    else:
        f.write("- Cả hai mô hình đều có hiệu suất tương đương và có thể được sử dụng tùy theo mục tiêu cụ thể của dự án.\n")
    
    f.write("\nBáo cáo được tạo tự động bằng Python.")

print(f"\nĐã tạo báo cáo đầy đủ tại {output_dir}/GiaLai_Model_Comparison_Report.txt")
print(f"Đã tạo các biểu đồ trực quan và lưu trong thư mục {output_dir}")
print("Phân tích hoàn tất!") 