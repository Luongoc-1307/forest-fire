# Dự án Xây dựng Bản đồ Dự đoán Nguy cơ Cháy rừng tại tỉnh Gia Lai, Việt Nam

## I. Tổng quan Dự án (Dành cho sinh viên trong ngành cần củng cố kiến thức)

### 1. Bối cảnh và Tầm quan trọng của Vấn đề Cháy rừng

Cháy rừng là một loại hình thiên tai gây ra các tác động tiêu cực và sâu rộng đến hệ sinh thái, kinh tế và xã hội. Dưới góc độ chuyên ngành:
*   **Viễn thám (Remote Sensing - RS):** Là khoa học và công nghệ thu thập thông tin về một đối tượng hoặc hiện tượng mà không cần tiếp xúc trực tiếp với nó. Trong quản lý cháy rừng, RS cung cấp dữ liệu không gian liên tục, bao phủ rộng lớn về các yếu tố như thảm thực vật, nhiệt độ bề mặt, và phát hiện điểm cháy.
*   **Hệ thống Thông tin Địa lý (Geographic Information System - GIS):** Là công cụ để thu thập, lưu trữ, quản lý, phân tích và hiển thị dữ liệu không gian. GIS giúp tích hợp các lớp dữ liệu khác nhau (viễn thám, địa hình, khí tượng, kinh tế-xã hội) để tạo ra các mô hình dự đoán và bản đồ nguy cơ.
*   **Học máy (Machine Learning - ML):** Là một nhánh của trí tuệ nhân tạo, nơi các thuật toán cho phép máy tính "học" từ dữ liệu để đưa ra dự đoán hoặc quyết định mà không cần được lập trình một cách tường minh cho từng trường hợp.

Tỉnh Gia Lai, với đặc điểm khí hậu mùa khô rõ rệt và diện tích rừng lớn, là một trong những khu vực có nguy cơ cháy rừng cao tại Việt Nam. Việc xây dựng mô hình dự đoán sớm và chính xác nguy cơ cháy là cực kỳ cần thiết để hỗ trợ công tác phòng chống, giảm thiệt hại. Nghiên cứu này tập trung vào mùa khô dự kiến từ tháng 12/2024 đến tháng 04/2025.

### 2. Mục tiêu Nghiên cứu

Nghiên cứu này nhằm đạt được các mục tiêu chính sau:

1.  **Ứng dụng Viễn thám và GIS:** Thu thập và tiền xử lý các bộ dữ liệu đa nguồn từ vệ tinh (quang học, nhiệt) và các nguồn dữ liệu phụ trợ (địa hình, khí tượng) bằng công cụ GIS và nền tảng điện toán đám mây **Google Earth Engine (GEE)**. GEE là một nền tảng mạnh mẽ cho phép truy cập và xử lý lượng lớn dữ liệu không gian địa lý mà không cần tải về máy.
2.  **Xây dựng Mô hình Học máy:** Huấn luyện và đánh giá các mô hình học máy (cụ thể là **Random Forest - RF** và **Gradient Tree Boosting - GTB**) để dự đoán xác suất xảy ra cháy rừng.
3.  **Thành lập Bản đồ Nguy cơ Cháy rừng:** Tạo ra các bản đồ phân vùng nguy cơ cháy rừng chi tiết cho tỉnh Gia Lai, với các cấp độ nguy cơ khác nhau, phục vụ công tác quản lý và phòng ngừa.

### 3. Quy trình Thực hiện Chi tiết

Quy trình nghiên cứu bao gồm các bước cốt lõi sau:

**Bước 1: Thu thập và Lựa chọn Dữ liệu (Data Acquisition and Selection)**

Việc lựa chọn các biến đầu vào (predictor variables hay features) là rất quan trọng, dựa trên hiểu biết về các yếu tố ảnh hưởng đến cháy rừng và tính sẵn có của dữ liệu.

*   **Dữ liệu Viễn thám:**
    *   **Ảnh vệ tinh Sentinel-2 (MSI - MultiSpectral Instrument):** Cung cấp các kênh phổ ở độ phân giải không gian cao (10m, 20m, 60m). Từ đây, chúng ta tính toán các **chỉ số thực vật (Vegetation Indices - VIs)** và **chỉ số độ ẩm (Moisture Indices)**. Sentinel-2 thuộc chương trình Copernicus của châu Âu, dữ liệu sản phẩm `COPERNICUS/S2_SR` là ảnh đã được hiệu chỉnh phản xạ bề mặt (Surface Reflectance).
    *   **Dữ liệu MODIS (Moderate Resolution Imaging Spectroradiometer):**
        *   **Nhiệt độ bề mặt đất (Land Surface Temperature - LST):** Sản phẩm `MODIS/061/MOD11A2` (độ phân giải 1km) cung cấp thông tin về nhiệt độ, một yếu tố quan trọng.
        *   **Điểm cháy lịch sử (Active Fire/Hotspot):** Sản phẩm `MODIS/061/MOD14A1` (độ phân giải 500m cho pixel phát hiện) được sử dụng để xác định vị trí các đám cháy đã xảy ra. Chúng ta dùng trường `FireMask > 6` để tăng độ tin cậy, coi đây là "nhãn" (label) cho việc huấn luyện mô hình: nơi có cháy (1) và không có cháy (0).
*   **Dữ liệu Địa hình (Topographic Data):**
    *   **Mô hình số độ cao SRTM (Shuttle Radar Topography Mission - DEM):** Sản phẩm `USGS/SRTMGL1_003` (độ phân giải 30m) được dùng để tính toán **độ cao (Elevation)**, **độ dốc (Slope)**, và **hướng dốc (Aspect)**. Các yếu tố này ảnh hưởng đến vi khí hậu và tốc độ lan truyền lửa.
*   **Dữ liệu Khí tượng (Meteorological Data):**
    *   **Lượng mưa (Precipitation):** Dữ liệu từ CHIRPS Daily (`UCSB-CHG/CHIRPS/DAILY`, độ phân giải ~5.5km) cho biết lượng mưa tích lũy hoặc tình trạng khô hạn.
    *   **Tốc độ gió (Wind Speed):** Dữ liệu từ ERA5 Land Daily Aggregated (`ECMWF/ERA5_LAND/DAILY_AGGR`, độ phân giải ~9km) là yếu tố quan trọng ảnh hưởng đến sự lan truyền của lửa.

**Giải thích:** Việc lựa chọn các nguồn dữ liệu này dựa trên các nghiên cứu trước đó và hiểu biết chuyên ngành về các yếu tố ảnh hưởng đến cháy rừng. Dữ liệu viễn thám cung cấp thông tin liên tục, khách quan và bao phủ diện rộng, rất phù hợp để giám sát các yếu tố môi trường như thảm thực vật, độ ẩm, nhiệt độ, và phát hiện điểm cháy. Dữ liệu địa hình và khí tượng bổ sung các yếu tố nền tảng về điều kiện tự nhiên, giúp mô hình hóa nguy cơ cháy một cách toàn diện hơn. Việc sử dụng các sản phẩm đã được hiệu chỉnh (như Sentinel-2 SR) giúp đảm bảo chất lượng và tính nhất quán của dữ liệu đầu vào.

**Bước 2: Tiền xử lý Dữ liệu (Data Preprocessing)**

Đây là bước làm sạch và chuẩn bị dữ liệu để đưa vào mô hình.

*   **Xử lý ảnh Sentinel-2:**
    *   **Lọc mây (Cloud Masking):** Loại bỏ các pixel bị ảnh hưởng bởi mây dựa trên kênh xác suất mây (`MSK_CLDPRB` < 30).
    *   **Tạo ảnh tổng hợp (Composite Image):** Sử dụng phương pháp tổng hợp trung vị (median composite) cho khoảng thời gian nghiên cứu (12/2024 - 04/2025) để có một ảnh đại diện, ít nhiễu cho mỗi pixel.
    *   **Cắt ảnh theo ranh giới (Clipping):** Giới hạn phạm vi xử lý trong địa phận tỉnh Gia Lai.
*   **Tính toán các biến dự báo (Predictor Variables):** Tổng cộng 15 biến được sử dụng:
    *   **Chỉ số thực vật:**
        *   **NDVI (Normalized Difference Vegetation Index):** Đo sức khỏe và mật độ thực vật. Công thức: (NIR - Red) / (NIR + Red).
        *   **EVI (Enhanced Vegetation Index):** Cải thiện NDVI, giảm ảnh hưởng của khí quyển và tín hiệu nền đất.
        *   **SAVI (Soil-Adjusted Vegetation Index):** Điều chỉnh NDVI cho các khu vực có độ che phủ thực vật thưa, giảm ảnh hưởng của đất nền.
        *   **VCI (Vegetation Condition Index):** So sánh NDVI hiện tại với NDVI dài hạn để đánh giá mức độ stress của thực vật.
        *   **TCI (Temperature Condition Index):** Tương tự VCI nhưng dựa trên Nhiệt độ Bề mặt Đất (LST), phản ánh stress nhiệt.
    *   **Chỉ số nước và độ ẩm:**
        *   **NDWI (Normalized Difference Water Index):** Phát hiện vực nước bề mặt. Thường dùng (Green - NIR) / (Green + NIR) hoặc các biến thể khác.
        *   **LSWI (Land Surface Water Index):** Nhạy cảm với tổng lượng nước trong thảm thực vật và đất. Thường dùng (NIR - SWIR) / (NIR + SWIR).
        *   **NDMI (Normalized Difference Moisture Index):** Tương tự LSWI, đo độ ẩm thực vật.
    *   **Chỉ số cháy/phục hồi:**
        *   **NBR (Normalized Burn Ratio):** Nhạy cảm với các khu vực bị cháy. Công thức: (NIR - SWIR2) / (NIR + SWIR2).
    *   **Biến địa hình:** DEM, Slope, Aspect (đã nêu ở trên).
    *   **Biến khí tượng:** Precipitation, Wind Speed (đã nêu ở trên).
    *   **Nhiệt độ bề mặt đất (LST):** Trực tiếp từ MODIS.
*   **Đồng bộ hóa độ phân giải (Resampling/Reprojection):**
    *   Dữ liệu đầu vào có **độ phân giải không gian (spatial resolution)** khác nhau (ví dụ: Sentinel-2 là 10-60m, LST là 1km).
    *   Để huấn luyện mô hình, các điểm mẫu được lấy ở độ phân giải 500m. Điều này có nghĩa là các raster có độ phân giải cao hơn (như Sentinel-2, DEM) sẽ được tổng hợp (aggregate) giá trị lên ô 500m (ví dụ, lấy trung bình), trong khi các raster có độ phân giải thấp hơn (LST, mưa, gió) sẽ được lấy giá trị tại pixel tương ứng (hoặc nội suy nếu cần thiết, nhưng thường GEE sẽ xử lý việc này khi lấy mẫu).
    *   Đối với bản đồ dự đoán cuối cùng, tất cả các lớp raster biến dự báo được **nội suy (interpolated)** về cùng độ phân giải 30m, sử dụng phương pháp **nội suy song tuyến tính (bilinear interpolation)**. Phương pháp này tính giá trị của pixel mới dựa trên giá trị của 4 pixel láng giềng gần nhất trong raster gốc, tạo ra kết quả mượt hơn so với phương pháp láng giềng gần nhất.

**Giải thích:** Tiền xử lý dữ liệu là bước bắt buộc để đảm bảo dữ liệu đầu vào sạch, nhất quán và phù hợp với yêu cầu của mô hình học máy. Lọc mây giúp loại bỏ nhiễu do mây che phủ, vốn là vấn đề phổ biến trong ảnh vệ tinh quang học. Tạo ảnh tổng hợp trung vị giúp giảm ảnh hưởng của các giá trị ngoại lai và tạo ra đại diện ổn định cho từng pixel trong thời gian nghiên cứu. Việc đồng bộ hóa độ phân giải là cần thiết vì các nguồn dữ liệu khác nhau có độ chi tiết khác nhau; nếu không đồng bộ, mô hình sẽ gặp khó khăn khi kết hợp các biến đầu vào. Nội suy song tuyến tính được chọn vì nó tạo ra các lớp raster mượt mà, giảm hiện tượng răng cưa hoặc mất thông tin khi chuyển đổi độ phân giải.

**Bước 3: Xây dựng và Huấn luyện Mô hình Học máy (Model Building and Training)**

Đây là bài toán **phân loại có giám sát (supervised classification)**, vì chúng ta có "nhãn" (cháy/không cháy) cho dữ liệu huấn luyện.

*   **Chuẩn bị dữ liệu huấn luyện và kiểm tra (Training and Test Data Preparation):**
    *   **Tạo lớp nhãn (Fire_Label):** Từ dữ liệu điểm cháy MODIS (`FireMask` > 6), các pixel được gán nhãn là 1 (cháy) hoặc 0 (không cháy).
    *   **Lấy mẫu phân tầng (Stratified Sampling):** 1000 điểm mẫu được thu thập trên toàn tỉnh Gia Lai ở độ phân giải 500m, sử dụng phương pháp `stratifiedSample` trong GEE. Phương pháp này đảm bảo tỷ lệ giữa các lớp (cháy/không cháy) trong mẫu tương tự như trong thực tế (hoặc theo một tỷ lệ mong muốn), giúp mô hình học tốt hơn với các lớp không cân bằng.
    *   **Chia dữ liệu (Data Splitting):** 1000 điểm mẫu được chia ngẫu nhiên thành 70% cho tập huấn luyện (training set - khoảng 700 điểm) để "dạy" mô hình, và 30% cho tập kiểm tra (test set - khoảng 300 điểm) để đánh giá hiệu suất của mô hình trên dữ liệu mà nó chưa từng thấy.
*   **Lựa chọn và Huấn luyện Mô hình:**
    *   **Random Forest (RF):** Là một thuật toán học máy kiểu **ensemble learning** (học tập hợp). RF xây dựng nhiều **cây quyết định (decision trees)** một cách độc lập trong quá trình huấn luyện. Mỗi cây được huấn luyện trên một tập con dữ liệu được lấy mẫu có hoàn lại (bootstrap aggregating hay **bagging**) từ tập huấn luyện gốc, và ở mỗi nút của cây, một tập con ngẫu nhiên các biến dự báo được chọn để tìm điểm chia tốt nhất. Kết quả dự đoán cuối cùng là kết quả bỏ phiếu (cho bài toán phân loại) hoặc trung bình (cho bài toán hồi quy) từ tất cả các cây.
        *   Các tham số chính trong GEE: `numberOfTrees=100`, `minLeafPopulation=5` (số mẫu tối thiểu ở một nút lá), `bagFraction=0.7` (tỷ lệ mẫu con cho mỗi cây), `seed=42` (để đảm bảo kết quả có thể tái lặp).
    *   **Gradient Tree Boosting (GTB) hay Gradient Boosting Machine (GBM):** Cũng là một thuật toán ensemble learning, nhưng thuộc họ **boosting**. GTB xây dựng các cây quyết định một cách tuần tự. Mỗi cây mới được huấn luyện để sửa lỗi (cụ thể là phần dư - residuals) của các cây trước đó. Nó sử dụng **gradient descent** để tối ưu hóa hàm mất mát.
        *   Các tham số chính trong GEE: `numberOfTrees=100`, `shrinkage=0.05` (tốc độ học - learning rate, kiểm soát sự đóng góp của mỗi cây), `samplingRate=0.7` (tỷ lệ mẫu con, tương tự bagging nhưng thường không hoàn lại), `maxNodes=10` (số nút tối đa cho mỗi cây, kiểm soát độ phức tạp của cây), `seed=42`.
    *   Mô hình được huấn luyện ở chế độ `PROBABILITY` để tạo bản đồ xác suất cháy và `CLASSIFICATION` để đánh giá trên tập kiểm tra.

**Giải thích:** Việc tạo lớp nhãn từ dữ liệu điểm cháy MODIS giúp mô hình học được mối liên hệ giữa các biến đầu vào và khả năng xảy ra cháy thực tế. Lấy mẫu phân tầng đảm bảo mô hình không bị thiên lệch do mất cân bằng giữa số lượng điểm cháy và không cháy (vì cháy rừng là hiện tượng hiếm). Chia dữ liệu thành tập huấn luyện và kiểm tra giúp đánh giá khách quan hiệu suất mô hình trên dữ liệu chưa từng thấy. Việc chọn RF và GTB là do hai mô hình này đã được chứng minh hiệu quả trong các bài toán phân loại môi trường, có khả năng xử lý dữ liệu nhiều chiều, phi tuyến tính, và cung cấp thông tin về độ quan trọng của biến. Các tham số được chọn dựa trên kinh nghiệm thực tiễn và khuyến nghị từ tài liệu GEE, đảm bảo mô hình vừa đủ phức tạp để học tốt nhưng không quá phức tạp gây overfitting.

**Bước 4: Đánh giá Hiệu suất Mô hình (Model Evaluation)**

Đánh giá độ chính xác của mô hình là bước không thể thiếu.

*   **Ma trận nhầm lẫn (Confusion Matrix):** Được tạo ra trên tập kiểm tra (30% dữ liệu). Ma trận này cho biết:
    *   **True Positives (TP):** Số điểm cháy thực tế được dự đoán đúng là cháy.
    *   **True Negatives (TN):** Số điểm không cháy thực tế được dự đoán đúng là không cháy.
    *   **False Positives (FP) / Type I Error:** Số điểm không cháy thực tế nhưng bị dự đoán nhầm là cháy.
    *   **False Negatives (FN) / Type II Error:** Số điểm cháy thực tế nhưng bị dự đoán nhầm là không cháy.
*   **Các chỉ số thống kê:**
    *   **Độ chính xác tổng thể (Overall Accuracy):** (TP + TN) / (TP + TN + FP + FN). Tỷ lệ dự đoán đúng.
    *   **Độ chính xác cho lớp cháy (Precision_fire):** TP / (TP + FP). Trong số những điểm được dự đoán là cháy, bao nhiêu điểm thực sự cháy.
    *   **Độ nhạy cho lớp cháy (Recall_fire / Sensitivity):** TP / (TP + FN). Trong số những điểm thực sự cháy, mô hình phát hiện được bao nhiêu điểm.
    *   **F1-Score (cho lớp cháy):** 2 * (Precision_fire * Recall_fire) / (Precision_fire + Recall_fire). Số trung bình điều hòa của Precision và Recall, hữu ích khi các lớp không cân bằng.
*   **Kiểm định chéo K-fold (K-fold Cross-Validation):**
    *   Thực hiện trên tập huấn luyện (70% dữ liệu). Tập huấn luyện được chia thành K phần (ở đây là 5-fold). Mô hình được huấn luyện K lần, mỗi lần sử dụng K-1 phần để huấn luyện và 1 phần còn lại để kiểm tra. Kết quả là trung bình của K lần đánh giá.
    *   **Mục đích:** Cung cấp một ước lượng đáng tin cậy hơn về hiệu suất của mô hình trên dữ liệu mới, giúp phát hiện **quá khớp (overfitting)**. Overfitting xảy ra khi mô hình học quá tốt trên dữ liệu huấn luyện (nhớ cả nhiễu) nhưng lại hoạt động kém trên dữ liệu chưa thấy.

**Giải thích:** Các chỉ số đánh giá như ma trận nhầm lẫn, độ chính xác, precision, recall, F1-score là các thước đo tiêu chuẩn trong học máy để đánh giá hiệu quả của mô hình phân loại. Chúng giúp xác định mô hình có dự đoán tốt cả hai lớp (cháy/không cháy) hay không, và có bị thiên lệch về một phía không. Kiểm định chéo K-fold giúp kiểm tra khả năng tổng quát hóa của mô hình, giảm nguy cơ đánh giá sai do chia dữ liệu ngẫu nhiên một lần duy nhất. Đây là bước quan trọng để đảm bảo mô hình không chỉ hoạt động tốt trên dữ liệu huấn luyện mà còn trên dữ liệu mới.

**Bước 5: Tạo Bản đồ Dự đoán Nguy cơ Cháy rừng (Fire Risk Mapping)**

*   Mô hình đã huấn luyện (RF và GTB) được áp dụng lên chồng dữ liệu 15 biến dự báo đã được đồng nhất về độ phân giải không gian 30m cho toàn bộ tỉnh Gia Lai.
*   Kết quả là các bản đồ raster, mỗi pixel (ô 30x30m) chứa giá trị xác suất xảy ra cháy (từ 0 đến 1) hoặc một lớp nguy cơ (ví dụ, phân thành 5 cấp: Thấp, Trung bình, Cao, Nguy hiểm, Cực kỳ nguy hiểm dựa trên các ngưỡng xác suất).

**Giải thích:** Việc tạo bản đồ nguy cơ cháy rừng là mục tiêu cuối cùng của dự án, giúp trực quan hóa kết quả mô hình và hỗ trợ ra quyết định cho các cơ quan quản lý. Việc sử dụng độ phân giải 30m cho bản đồ đầu ra giúp cân bằng giữa chi tiết không gian và khả năng xử lý dữ liệu lớn. Phân cấp nguy cơ thành nhiều mức giúp các nhà quản lý ưu tiên nguồn lực cho các khu vực nguy hiểm nhất, thay vì phải xử lý toàn bộ diện tích rừng một cách đồng đều.

### 4. Phân tích Kết quả (Results Analysis)

*   **So sánh hiệu suất mô hình:**
    *   RF đạt Overall Accuracy 93.05% và F1-Score (lớp cháy) 0.9317 trên tập kiểm tra.
    *   GTB đạt Overall Accuracy 83.81% và F1-Score (lớp cháy) 0.8412 trên tập kiểm tra.
    *   Cross-validation 5-fold trên tập huấn luyện: RF đạt ~77.90%, GTB đạt ~77.28%.
    *   **Nhận xét:** RF hoạt động tốt hơn trên tập kiểm tra cụ thể, nhưng sự chênh lệch lớn giữa hiệu suất tập kiểm tra và cross-validation của RF (93.05% vs 77.90%) so với GTB (83.81% vs 77.28%) cho thấy RF có thể đã bị overfitting nhiều hơn một chút so với GTB trên cấu trúc dữ liệu huấn luyện/kiểm tra này. GTB có vẻ tổng quát hóa tốt hơn.
*   **Độ quan trọng của biến (Feature Importance):**
    *   Cả hai mô hình đều cho phép đánh giá mức độ đóng góp của từng biến vào việc dự đoán.
    *   **RF:** Top 5 là Temperature, DEM, Precipitation, WindSpeed, NBR.
    *   **GTB:** Top 5 là Temperature, WindSpeed, Precipitation, DEM, EVI.
    *   **Nhận xét:** Nhiệt độ bề mặt đất (LST/Temperature), Độ cao (DEM), Lượng mưa (Precipitation), và Tốc độ gió (WindSpeed) là các yếu tố chủ đạo. Các chỉ số thực vật truyền thống như NDVI không nằm trong top đầu, có thể do đặc điểm mùa khô ở Gia Lai làm giảm sự khác biệt của NDVI.
*   **Phân tích bản đồ nguy cơ:**
    *   Cả hai mô hình tạo ra bản đồ nguy cơ với 5 cấp độ.
    *   RF: Cấp "Cao" chiếm 55.8%, "Cực kỳ nguy hiểm" chiếm 0.1%.
    *   GTB: Cấp "Cao" chiếm 38.9%, "Cực kỳ nguy hiểm" chiếm 2.1%.
    *   Vị trí các vùng nguy cơ cao chủ yếu ở trung tâm và phía đông tỉnh. Bản đồ RF có vẻ "mịn" hơn.
*   **Đối chiếu với điểm cháy thực tế:** Phần lớn các điểm cháy MODIS thực tế (dùng làm nhãn) nằm trong các vùng được dự đoán có nguy cơ cao đến rất cao, đặc biệt là với mô hình RF, khẳng định tính hữu dụng của mô hình.

### 5. Kết luận và Hướng phát triển

*   **Kết luận chính:** Nghiên cứu đã chứng minh tiềm năng của việc tích hợp RS, GIS và ML (RF, GTB) trên nền tảng GEE để xây dựng bản đồ nguy cơ cháy rừng hiệu quả cho Gia Lai. Các yếu tố khí tượng và địa hình đóng vai trò then chốt.
*   **Ý nghĩa thực tiễn:** Bản đồ nguy cơ là công cụ hỗ trợ ra quyết định cho cơ quan quản lý trong công tác phòng chống cháy rừng.
*   **Hạn chế và Hướng phát triển:**
    *   **Chất lượng dữ liệu nhãn:** Độ chính xác của điểm cháy MODIS có thể ảnh hưởng đến mô hình.
    *   **Độ phân giải dữ liệu đầu vào:** Sự khác biệt về độ phân giải và việc nội suy có thể ảnh hưởng đến độ chính xác chi tiết của bản đồ.
    *   **Hướng phát triển:**
        1.  **Tích hợp yếu tố kinh tế-xã hội:** Mật độ dân số, đường giao thông, loại hình sử dụng đất chi tiết, các hoạt động của con người.
        2.  **Mô hình dự báo động (Dynamic Modeling):** Xây dựng mô hình dự báo theo thời gian thực hoặc ngắn hạn.
        3.  **Kiểm chứng thực địa (Ground Truthing):** Xác minh kết quả mô hình bằng khảo sát thực địa.
        4.  **Mở rộng phạm vi:** Áp dụng cho các khu vực khác.

Đây là một cái nhìn tổng quan chi tiết hơn về dự án, hy vọng sẽ giúp bạn củng cố kiến thức về các khái niệm và quy trình đã được áp dụng!

---

## II. Phần Hỏi và Đáp (Giống như một buổi bảo vệ đồ án)

Dưới đây là một số câu hỏi mà một giáo sư có thể đặt ra để đánh giá sự hiểu biết của sinh viên về dự án, cùng với câu trả lời chi tiết.

---

**Câu hỏi 1: Tại sao nhóm lại chọn tỉnh Gia Lai làm khu vực nghiên cứu mà không phải một tỉnh khác? Các đặc điểm nổi bật nào của Gia Lai khiến nó phù hợp với đề tài này?**

**Trả lời:**

Nhóm chúng em chọn tỉnh Gia Lai vì một số lý do chính sau:

1.  **Điểm nóng về cháy rừng:** Gia Lai, nằm ở khu vực Tây Nguyên, là một trong những tỉnh có nguy cơ cháy rừng cao ở Việt Nam. Tỉnh có diện tích rừng lớn, bao gồm cả rừng tự nhiên và rừng trồng, với thảm thực vật đa dạng. Đặc biệt, sự hiện diện của rừng khộp (rừng lá rộng rụng lá) đặc trưng của Tây Nguyên rất dễ bắt lửa vào mùa khô.
2.  **Điều kiện khí hậu khắc nghiệt:** Khí hậu Gia Lai mang đặc trưng của khí hậu nhiệt đới gió mùa cao nguyên, chia thành hai mùa rõ rệt: mùa mưa và mùa khô. Mùa khô thường kéo dài từ tháng 11 đến tháng 4 năm sau, với lượng mưa rất thấp, độ ẩm không khí giảm mạnh và nhiệt độ cao. Đây chính là thời kỳ cao điểm của nguy cơ cháy rừng, và cũng là giai đoạn mà nghiên cứu của chúng em tập trung vào (tháng 12/2024 - 04/2025).
3.  **Địa hình đa dạng:** Gia Lai có địa hình phức tạp, bao gồm cao nguyên, núi thấp và thung lũng. Sự đa dạng này ảnh hưởng đến vi khí hậu, hướng gió, tốc độ lan truyền của đám cháy và khả năng tiếp cận của lực lượng chữa cháy, làm cho việc mô hình hóa nguy cơ cháy trở nên thách thức nhưng cũng rất cần thiết.
4.  **Tầm quan trọng kinh tế - xã hội và môi trường:** Rừng ở Gia Lai đóng vai trò quan trọng trong việc duy trì cân bằng sinh thái, bảo vệ nguồn nước, và là sinh kế của nhiều cộng đồng địa phương. Thiệt hại do cháy rừng không chỉ ảnh hưởng đến môi trường mà còn gây tổn thất lớn về kinh tế và xã hội.
5.  **Tính sẵn có của dữ liệu:** Các nguồn dữ liệu viễn thám cần thiết cho nghiên cứu (như Sentinel-2, MODIS, SRTM DEM, dữ liệu mưa CHIRPS, dữ liệu gió ERA5) đều có độ bao phủ tốt và chất lượng đảm bảo cho khu vực tỉnh Gia Lai trên nền tảng Google Earth Engine, tạo điều kiện thuận lợi cho việc thu thập và xử lý.

Những đặc điểm này không chỉ làm cho Gia Lai trở thành một khu vực có nguy cơ cháy rừng đáng kể mà còn là một "phòng thí nghiệm" tự nhiên lý tưởng để thử nghiệm và ứng dụng các mô hình dự đoán tiên tiến, từ đó cung cấp những kết quả có giá trị thực tiễn cao.

---

**Câu hỏi 2: Nhóm đã sử dụng 15 biến đầu vào. Cơ sở nào để các bạn lựa chọn những biến này? Tại sao lại là 15 biến mà không phải ít hơn hay nhiều hơn? Có biến nào các bạn đã cân nhắc nhưng cuối cùng lại loại bỏ không, và tại sao?**

**Trả lời:**

Việc lựa chọn 15 biến đầu vào được dựa trên ba cơ sở chính:

1.  **Tổng quan tài liệu khoa học (Literature Review):** Chúng em đã tham khảo nhiều nghiên cứu trước đây trong và ngoài nước về dự đoán nguy cơ cháy rừng sử dụng viễn thám và học máy. Các nghiên cứu này đã chỉ ra rằng các yếu tố liên quan đến **thảm thực vật, độ ẩm, địa hình, và điều kiện khí tượng** là những nhân tố chính ảnh hưởng đến khả năng bùng phát và lan truyền của cháy rừng. 15 biến được chọn đều thuộc các nhóm này:
    *   **Chỉ số thực vật:**
        *   **NDVI (Normalized Difference Vegetation Index):** Đo sức khỏe và mật độ thực vật. Công thức: (NIR - Red) / (NIR + Red).
        *   **EVI (Enhanced Vegetation Index):** Cải thiện NDVI, giảm ảnh hưởng của khí quyển và tín hiệu nền đất.
        *   **SAVI (Soil-Adjusted Vegetation Index):** Điều chỉnh NDVI cho các khu vực có độ che phủ thực vật thưa, giảm ảnh hưởng của đất nền.
        *   **VCI (Vegetation Condition Index):** So sánh NDVI hiện tại với NDVI dài hạn để đánh giá mức độ stress của thực vật.
        *   **TCI (Temperature Condition Index):** Tương tự VCI nhưng dựa trên Nhiệt độ Bề mặt Đất (LST), phản ánh stress nhiệt.
    *   **Chỉ số nước và độ ẩm:**
        *   **NDWI (Normalized Difference Water Index):** Phát hiện vực nước bề mặt. Thường dùng (Green - NIR) / (Green + NIR) hoặc các biến thể khác.
        *   **LSWI (Land Surface Water Index):** Nhạy cảm với tổng lượng nước trong thảm thực vật và đất. Thường dùng (NIR - SWIR) / (NIR + SWIR).
        *   **NDMI (Normalized Difference Moisture Index):** Tương tự LSWI, đo độ ẩm thực vật.
    *   **Chỉ số cháy/phục hồi:**
        *   **NBR (Normalized Burn Ratio):** Nhạy cảm với các khu vực bị cháy. Công thức: (NIR - SWIR2) / (NIR + SWIR2).
    *   **Biến địa hình:** DEM, Slope, Aspect (đã nêu ở trên).
    *   **Biến khí tượng:** Precipitation, Wind Speed (đã nêu ở trên).
    *   **Nhiệt độ bề mặt đất (LST):** Trực tiếp từ MODIS.
2.  **Tính sẵn có và chất lượng dữ liệu trên Google Earth Engine (GEE):** Các biến này được lựa chọn vì chúng có thể được tính toán hoặc thu thập một cách hiệu quả từ các bộ dữ liệu viễn thám phổ biến và đáng tin cậy có sẵn trên GEE như Sentinel-2, MODIS, SRTM, CHIRPS, ERA5 Land. Điều này đảm bảo tính khả thi và khả năng tái lặp của nghiên cứu.
3.  **Đặc điểm của khu vực nghiên cứu:** Các biến được chọn được cho là phù hợp để phản ánh các điều kiện đặc thù của Gia Lai, một tỉnh có mùa khô rõ rệt và địa hình đa dạng.

**Về số lượng biến:**

*   **Không phải ít hơn:** Việc sử dụng một bộ biến đa dạng giúp mô hình có cái nhìn toàn diện hơn về các yếu tố gây cháy. Nếu sử dụng quá ít biến, mô hình có thể bỏ sót những thông tin quan trọng và dẫn đến dự đoán kém chính xác (underfitting).
*   **Không phải nhiều hơn (một cách không cần thiết):** Mặc dù có thể thêm nhiều biến hơn, nhưng việc này có thể dẫn đến hiện tượng "lời nguyền số chiều" (curse of dimensionality), làm tăng độ phức tạp tính toán, nguy cơ đa cộng tuyến (multicollinearity) giữa các biến, và có thể gây nhiễu cho mô hình nếu các biến thêm vào không thực sự liên quan (overfitting). 15 biến này được coi là một tập hợp khá toàn diện nhưng vẫn quản lý được.

**Về các biến đã cân nhắc nhưng loại bỏ:**

Trong quá trình nghiên cứu ban đầu, chúng em có cân nhắc một số yếu tố khác như:

*   **Khoảng cách đến đường giao thông, khu dân cư:** Đây là các yếu tố liên quan đến hoạt động của con người, một trong những nguyên nhân chính gây cháy rừng. Tuy nhiên, việc thu thập và đồng bộ hóa dữ liệu này ở quy mô toàn tỉnh với độ chính xác cao và cập nhật đòi hỏi nhiều nỗ lực hơn và có thể nằm ngoài phạm vi của GEE cho xử lý tự động hoàn toàn. Đồng thời, việc đưa quá nhiều yếu tố không gian địa lý tĩnh có thể làm mô hình thiên về các đặc điểm cố định thay vì các điều kiện động của môi trường.
*   **Loại hình sử dụng đất/lớp phủ đất chi tiết:** Mặc dù có liên quan, nhưng việc tạo ra một bản đồ lớp phủ đất chi tiết, chính xác và cập nhật cho toàn tỉnh cũng là một nhiệm vụ lớn. Thay vào đó, các chỉ số thực vật và độ ẩm từ vệ tinh đã gián tiếp phản ánh được tình trạng và loại hình thảm thực vật ở một mức độ nhất định.

Chúng em quyết định tập trung vào các yếu tố có thể trích xuất trực tiếp và hiệu quả từ dữ liệu viễn thám và khí tượng sẵn có trên GEE để đảm bảo tính tự động hóa và khả năng áp dụng nhanh chóng của quy trình. Việc tích hợp các yếu tố kinh tế-xã hội và lớp phủ đất chi tiết hơn được xem là một hướng phát triển tiềm năng cho các nghiên cứu tiếp theo.

---

**Câu hỏi 3: Nhóm đã sử dụng hai mô hình là Random Forest (RF) và Gradient Tree Boosting (GTB). Tại sao lại chọn hai mô hình này? Ưu nhược điểm của từng mô hình trong bài toán dự đoán nguy cơ cháy rừng là gì? Kết quả cho thấy RF tốt hơn trên tập test nhưng GTB lại có vẻ tổng quát hóa tốt hơn qua cross-validation. Nhóm giải thích hiện tượng này như thế nào?**

**Trả lời:**

Chúng em chọn Random Forest (RF) và Gradient Tree Boosting (GTB) vì một số lý do sau:

1.  **Hiệu suất cao đã được chứng minh:** Cả RF và GTB đều là các thuật toán học máy dựa trên cây quyết định (ensemble learning) nổi tiếng với hiệu suất mạnh mẽ trong nhiều bài toán phân loại và hồi quy, bao gồm cả các ứng dụng trong khoa học môi trường và dự đoán thiên tai. Chúng có khả năng xử lý tốt các bộ dữ liệu lớn, nhiều chiều và có mối quan hệ phi tuyến tính giữa các biến.
2.  **Khả năng xử lý dữ liệu hỗn hợp:** Chúng có thể làm việc với cả dữ liệu dạng số (như nhiệt độ, độ dốc) và dữ liệu dạng hạng mục (mặc dù trong nghiên cứu này chủ yếu là dữ liệu số sau khi tính toán chỉ số).
3.  **Ít yêu cầu về tiền xử lý phức tạp:** So với một số mô hình khác (ví dụ SVM với kernel, hay Neural Networks), RF và GTB thường ít nhạy cảm hơn với việc chuẩn hóa dữ liệu (scaling) và có khả năng xử lý giá trị ngoại lai (outliers) một cách tương đối tốt.
4.  **Cung cấp độ quan trọng của biến (Feature Importance):** Cả hai mô hình đều cung cấp thông tin về mức độ đóng góp của từng biến vào việc dự đoán.
5.  **Sẵn có trên Google Earth Engine:** Cả RF và GTB đều được tích hợp sẵn trong GEE, giúp việc huấn luyện và áp dụng mô hình trên dữ liệu không gian địa lý quy mô lớn trở nên thuận tiện.

**Ưu nhược điểm của từng mô hình trong bài toán này:**

*   **Random Forest (RF):**
    *   **Ưu điểm:**
        *   **Chống overfitting tốt:** Do cơ chế bagging (tạo nhiều cây từ các mẫu con ngẫu nhiên) và chọn ngẫu nhiên một tập con các biến ở mỗi nút tách, RF thường ít bị overfitting hơn so với một cây quyết định đơn lẻ.
        *   **Xử lý song song hiệu quả:** Các cây trong RF có thể được xây dựng độc lập, giúp tăng tốc độ huấn luyện trên các hệ thống đa lõi.
        *   **Ổn định và dễ sử dụng:** Ít tham số cần tinh chỉnh hơn so với GTB.
    *   **Nhược điểm:**
        *   **Có thể kém chính xác hơn GTB trên một số bộ dữ liệu:** Do các cây được xây dựng độc lập, RF có thể không "học" được các mối quan hệ phức tạp bằng GTB, vốn xây dựng cây một cách tuần tự để sửa lỗi.
        *   **Mô hình "hộp đen" hơn:** Mặc dù cung cấp độ quan trọng của biến, việc diễn giải cách thức hoạt động của hàng trăm cây riêng lẻ là khó khăn.

*   **Gradient Tree Boosting (GTB):**
    *   **Ưu điểm:**
        *   **Thường cho độ chính xác rất cao:** Bằng cách xây dựng các cây tuần tự, mỗi cây sau cố gắng sửa lỗi của các cây trước đó, GTB thường đạt được hiệu suất dự đoán vượt trội.
        *   **Linh hoạt:** Có nhiều tham số để tinh chỉnh (ví dụ: learning rate, max depth, subsample rate), cho phép tối ưu hóa mô hình tốt hơn cho từng bài toán cụ thể.
    *   **Nhược điểm:**
        *   **Dễ bị overfitting hơn RF nếu không được tinh chỉnh cẩn thận:** Nếu số lượng cây quá lớn hoặc learning rate quá cao, GTB có thể học quá sát dữ liệu huấn luyện.
        *   **Thời gian huấn luyện lâu hơn:** Do tính tuần tự, việc xây dựng mô hình GTB thường tốn nhiều thời gian hơn RF, đặc biệt với dữ liệu lớn.
        *   **Nhạy cảm hơn với các tham số:** Việc lựa chọn tham số phù hợp quan trọng hơn và đòi hỏi nhiều kinh nghiệm hơn.

**Giải thích hiện tượng RF tốt hơn trên tập test nhưng GTB tổng quát hóa tốt hơn qua cross-validation:**

Kết quả của chúng em cho thấy RF có Overall Accuracy là 93.05% và F1-score là 0.9317 trên tập kiểm tra, cao hơn GTB (83.81% và 0.8412). Tuy nhiên, kết quả 5-fold cross-validation trên tập huấn luyện (training set) lại cho thấy độ chính xác trung bình khá tương đồng (RF: 77.90%, GTB: 77.28%). Điều này cho thấy GTB có vẻ tổng quát hóa tốt hơn một chút so với RF trên cấu trúc dữ liệu huấn luyện/kiểm tra này.

Hiện tượng này có thể được giải thích như sau:

1.  **Khả năng Overfitting của RF trên một cấu trúc dữ liệu cụ thể:** Tập kiểm tra (300 điểm) tuy được tách ngẫu nhiên nhưng vẫn có thể vô tình chứa những đặc điểm hoặc phân bố dữ liệu mà mô hình RF "học" được rất tốt trong quá trình huấn luyện trên 700 điểm của tập huấn luyện. RF, với bản chất tạo ra nhiều cây phức tạp, có thể đã "khớp" (fit) rất tốt với cấu trúc đặc thù của cả tập huấn luyện và tập kiểm tra cụ thể đó.
2.  **Sự phân chia dữ liệu:** Cách chia 70/30 có thể chưa đại diện hoàn hảo cho toàn bộ không gian đặc trưng. Kết quả cross-validation, vốn thực hiện việc chia và đánh giá nhiều lần trên các tập con khác nhau của tập huấn luyện, cung cấp một bức tranh đáng tin cậy hơn về khả năng tổng quát hóa của mô hình trên dữ liệu "chưa từng thấy" (unseen data) trong cùng một phân phối gốc.
3.  **Độ ổn định của GTB:** GTB, với cơ chế học tuần tự và điều chỉnh lỗi, có thể đã xây dựng được một mô hình ít phụ thuộc hơn vào những đặc thù của một tập con dữ liệu cụ thể. Tốc độ học (`shrinkage = 0.05`) và giới hạn số nút (`maxNodes = 10`) trong GTB cũng là các biện pháp giúp kiểm soát overfitting. Sự khác biệt không quá lớn giữa hiệu suất trên tập test và cross-validation của GTB (83.81% so với 77.28%) so với RF (93.05% so với 77.90%) cho thấy điều này. RF có một "bước nhảy" lớn hơn, gợi ý rằng hiệu suất cao trên tập test có thể một phần là do nó "may mắn" phù hợp với tập test đó.
4.  **Tham số mô hình:** Các tham số được chọn cho RF và GTB trong GEE là các giá trị khá phổ thông. Có thể việc tinh chỉnh kỹ hơn các tham số (hyperparameter tuning) cho từng mô hình (ví dụ, sử dụng Grid Search hoặc Random Search bên ngoài GEE nếu có dữ liệu xuất ra) sẽ cho kết quả khác hoặc làm rõ hơn về khả năng của từng mô hình.

Tóm lại, trong khi RF đạt kết quả rất ấn tượng trên một lần chia dữ liệu kiểm tra cụ thể, kết quả cross-validation cho thấy GTB có thể là mô hình ổn định hơn và có khả năng tổng quát hóa tốt hơn một chút khi đối mặt với các tập dữ liệu mới có thể hơi khác biệt so với tập huấn luyện ban đầu. Điều này nhấn mạnh tầm quan trọng của cross-validation trong việc đánh giá mô hình một cách toàn diện. Dựa trên cả hai chỉ số, RF vẫn là một lựa chọn mạnh mẽ, nhưng cần lưu ý về khả năng nó có thể hơi "overfit" so với GTB trong trường hợp này.

---

**Câu hỏi 4: Trong phần thảo luận, nhóm có đề cập rằng các chỉ số thực vật truyền thống như NDVI không nằm trong top 5 biến quan trọng nhất. Điều này có vẻ hơi ngược với nhiều nghiên cứu khác. Nhóm có thể giải thích tại sao lại có kết quả như vậy ở khu vực Gia Lai không? Và biến nào là quan trọng nhất theo mô hình của các bạn?**

**Trả lời:**

Đúng là kết quả của chúng em cho thấy các chỉ số thực vật truyền thống như NDVI không nằm trong top đầu, có thể do đặc điểm mùa khô ở Gia Lai làm giảm sự khác biệt của NDVI.

**Biến quan trọng nhất:**

Dựa trên kết quả từ cả hai mô hình, **Nhiệt độ bề mặt đất (Temperature/LST)** là biến quan trọng nhất, luôn đứng đầu trong danh sách. Điều này hoàn toàn hợp lý vì nhiệt độ cao là một trong những điều kiện tiên quyết cho việc bốc hơi ẩm từ vật liệu cháy, làm tăng khả năng bắt lửa và tốc độ cháy.

Tóm lại, mặc dù NDVI quan trọng trong nhiều bối cảnh, nhưng tại Gia Lai trong mùa khô, các yếu tố trực tiếp liên quan đến sự khô hạn và khả năng lan truyền lửa như nhiệt độ, mưa, gió và đặc điểm địa hình dường như đóng vai trò chi phối hơn trong việc xác định nguy cơ cháy.

---

**Câu hỏi 5: Nhóm đã đề xuất một số hướng nghiên cứu tiếp theo, trong đó có "Tích hợp các yếu tố xã hội-kinh tế và hoạt động của con người". Nhóm có thể cho biết cụ thể hơn những yếu tố nào có thể được tích hợp và chúng có thể cải thiện mô hình dự đoán như thế nào không? Việc thu thập các dữ liệu này có những khó khăn gì?**

**Trả lời:**

Việc tích hợp các yếu tố xã hội-kinh tế và hoạt động của con người là một hướng đi rất quan trọng để nâng cao độ chính xác và tính thực tiễn của mô hình dự đoán nguy cơ cháy rừng. Con người vừa là nguyên nhân chính gây ra cháy rừng (vô ý hoặc cố ý), vừa là đối tượng chịu tác động của cháy.

**Các yếu tố xã hội-kinh tế và hoạt động con người cụ thể có thể tích hợp:**

1.  **Mật độ dân số và phân bố dân cư:**
    *   **Cách cải thiện:** Các khu vực có mật độ dân số cao hơn hoặc gần khu dân cư hơn có thể có nguy cơ cháy cao hơn do các hoạt động sinh hoạt, đốt rác, hoặc sự bất cẩn của con người.
    *   **Dữ liệu:** Dữ liệu điều tra dân số, bản đồ phân bố dân cư (ví dụ: WorldPop, LandScan).

2.  **Mạng lưới đường giao thông:**
    *   **Cách cải thiện:** Khoảng cách đến đường bộ, đường sắt. Đường giao thông tạo điều kiện cho con người tiếp cận rừng, làm tăng nguy cơ cháy do vứt tàn thuốc, đốt thực bì ven đường, hoặc các hoạt động khác. Tuy nhiên, đường cũng giúp lực lượng chữa cháy tiếp cận nhanh hơn.
    *   **Dữ liệu:** Bản đồ giao thông từ OpenStreetMap, cơ quan quản lý giao thông.

3.  **Hoạt động nông nghiệp:**
    *   **Cách cải thiện:** Vị trí các khu vực canh tác nông nghiệp, đặc biệt là các hoạt động có sử dụng lửa như đốt nương làm rẫy, đốt rơm rạ sau thu hoạch.
    *   **Dữ liệu:** Bản đồ sử dụng đất nông nghiệp, thông tin mùa vụ từ cơ quan nông nghiệp.

4.  **Hoạt động du lịch và giải trí:**
    *   **Cách cải thiện:** Các khu du lịch sinh thái, điểm cắm trại, lối mòn đi bộ trong rừng. Hoạt động của du khách có thể vô tình gây cháy.
    *   **Dữ liệu:** Thông tin từ sở văn hóa du lịch, ban quản lý các khu du lịch.

5.  **Khai thác lâm sản và các hoạt động trong rừng khác:**
    *   **Cách cải thiện:** Các khu vực có hoạt động khai thác gỗ (hợp pháp hoặc bất hợp pháp), thu hái lâm sản phụ. Sự hiện diện của con người và các công cụ có thể làm tăng nguy cơ.
    *   **Dữ liệu:** Thông tin từ kiểm lâm, các công ty lâm nghiệp.

6.  **Lịch sử các vụ vi phạm về quản lý bảo vệ rừng:**
    *   **Cách cải thiện:** Các khu vực từng xảy ra phá rừng, lấn chiếm đất rừng có thể có nguy cơ cháy cao hơn do ý thức chấp hành pháp luật kém.
    *   **Dữ liệu:** Hồ sơ từ cơ quan kiểm lâm.

7.  **Trình độ dân trí, ý thức cộng đồng về phòng cháy chữa cháy:**
    *   **Cách cải thiện:** Yếu tố này khó định lượng trực tiếp bằng dữ liệu không gian, nhưng có thể được xem xét gián tiếp qua các chương trình tuyên truyền hoặc tỷ lệ vi phạm.
    *   **Dữ liệu:** Khảo sát xã hội học, báo cáo từ chính quyền địa phương.

**Khó khăn trong việc thu thập và tích hợp các dữ liệu này:**

1.  **Tính sẵn có và định dạng dữ liệu:** Nhiều loại dữ liệu xã hội-kinh tế không luôn có sẵn ở định dạng GIS hoặc không được cập nhật thường xuyên. Dữ liệu có thể nằm ở các cơ quan khác nhau, dưới dạng bảng biểu hoặc báo cáo văn bản, đòi hỏi nhiều công sức để số hóa và chuẩn hóa.
2.  **Độ chính xác và độ phân giải không gian:** Dữ liệu xã hội-kinh tế thường có độ phân giải không gian thấp hơn so với dữ liệu viễn thám (ví dụ, dữ liệu dân số ở cấp xã, huyện). Việc tích hợp với dữ liệu pixel 30m cần các phương pháp phân bổ (disaggregation) hợp lý và có thể làm tăng sự không chắc chắn.
3.  **Tính động của dữ liệu:** Các hoạt động của con người thay đổi theo thời gian (ví dụ: mùa vụ nông nghiệp, các dự án phát triển mới). Việc cập nhật liên tục các lớp dữ liệu này là một thách thức.
4.  **Bảo mật và quyền riêng tư:** Một số dữ liệu (ví dụ: thông tin chi tiết về hộ gia đình, các vụ vi phạm cụ thể) có thể nhạy cảm và khó tiếp cận.
5.  **Xác định mối quan hệ nhân quả:** Việc xác định chính xác mối quan hệ giữa một yếu tố xã hội-kinh tế cụ thể và nguy cơ cháy có thể phức tạp. Ví dụ, đường giao thông có thể vừa làm tăng nguy cơ (dễ tiếp cận để gây cháy) vừa làm giảm nguy cơ (dễ tiếp cận để chữa cháy). Mô hình cần có khả năng nắm bắt các mối quan hệ phức tạp này.
6.  **Tích hợp vào Google Earth Engine:** GEE mạnh về xử lý dữ liệu raster từ vệ tinh. Việc tải lên và xử lý các lớp dữ liệu vector hoặc bảng thuộc tính lớn về xã hội-kinh tế có thể có những hạn chế hoặc đòi hỏi quy trình làm việc phức tạp hơn.