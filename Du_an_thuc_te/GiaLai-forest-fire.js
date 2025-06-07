// Xác định vùng nghiên cứu (ROI) bằng FeatureCollection.
// Đây là một tài sản (asset) trong Google Earth Engine.
var gia_lai = ee.FeatureCollection("projects/ee-bonglantrungmuoi/assets/gia_lai");

// Thiết lập khoảng thời gian phân tích.
var startDate = "2024-12-01", endDate = "2025-04-30";

// Định nghĩa các tham số hiển thị cho từng lớp dữ liệu.
// Mỗi khóa đại diện cho một lớp dữ liệu cụ thể, giá trị tương ứng là một đối tượng
// chứa giá trị tối thiểu, tối đa và bảng màu để hiển thị trực quan.
var VIS_PARAMS = {
    ndvi: { min: 0, max: 1, palette: ['brown', 'yellow', 'green'] }, // Chỉ số khác biệt thực vật NDVI
    ndwi: { min: -1, max: 1, palette: ['brown', 'white', 'blue'] }, // Chỉ số khác biệt nước NDWI
    vci: { min: 0, max: 100, palette: ['red', 'yellow', 'green'] },   // Chỉ số điều kiện thực vật VCI
    tci: { min: 0, max: 100, palette: ['blue', 'white', 'red'] },    // Chỉ số điều kiện nhiệt độ TCI
    temp: { min: 15, max: 45, palette: ['blue', 'yellow', 'red'] },   // Nhiệt độ bề mặt đất LST
    dem: { min: 200, max: 1200, palette: ['green', 'brown', 'white'] }, // Mô hình số độ cao DEM
    slope: { min: 0, max: 60, palette: ['white', 'orange', 'red'] }, // Độ dốc địa hình
    fire: { min: 0, max: 1, palette: ['white', 'red'] },               // Mặt nạ cháy rừng
    prediction_5levels: { // Dự đoán nguy cơ cháy với 5 cấp độ
        min: 1, max: 5,
        palette: ['#00FF00', '#FFFF00', '#FFA500', '#FF0000', '#8B0000'] // Xanh lá, Vàng, Cam, Đỏ, Đỏ sẫm
    }
};

/**
 * Xử lý ảnh vệ tinh Sentinel-2 để tính toán các chỉ số thực vật.
 * @return {object} Đối tượng chứa ảnh Sentinel đã xử lý và các chỉ số dẫn xuất.
 */
function processSentinel() {
    // Tải bộ dữ liệu ảnh Sentinel-2 Surface Reflectance.
    var sentinel = ee.ImageCollection("COPERNICUS/S2_SR")
        .filterBounds(gia_lai) // Lọc theo vùng nghiên cứu.
        .filterDate(startDate, endDate) // Lọc theo khoảng thời gian đã định nghĩa.
        // Lọc ảnh có tỷ lệ điểm ảnh bị mây dưới 10%.
        .filterMetadata("CLOUDY_PIXEL_PERCENTAGE", "less_than", 10)
        // Áp dụng mặt nạ mây dựa trên kênh xác suất mây của Sentinel-2 (MSK_CLDPRB).
        // Chỉ giữ lại các điểm ảnh có xác suất mây dưới 30%.
        .map(function (image) {
            return image.updateMask(image.select("MSK_CLDPRB").lt(30));
        })
        // Chọn các kênh phổ cần thiết cho phân tích.
        .select(["B2", "B3", "B4", "B8", "B11", "B12"]) // Blue, Green, Red, NIR, SWIR1, SWIR2
        .median() // Tạo ảnh tổng hợp bằng cách lấy giá trị trung vị của tất cả ảnh.
        .clip(gia_lai); // Cắt ảnh tổng hợp theo vùng nghiên cứu.

    // Trả về đối tượng chứa ảnh đã xử lý và các chỉ số được tính toán.
    return {
        sentinel: sentinel, // Ảnh tổng hợp Sentinel-2 đã xử lý.
        // Tính chỉ số khác biệt thực vật chuẩn hóa NDVI.
        ndvi: sentinel.normalizedDifference(["B8", "B4"]).rename("NDVI"),
        // Tính chỉ số khác biệt nước chuẩn hóa NDWI.
        ndwi: sentinel.normalizedDifference(["B3", "B8"]).rename("NDWI"),
        // Tính chỉ số nước bề mặt đất LSWI.
        lswi: sentinel.normalizedDifference(["B8", "B11"]).rename("LSWI"),
        // Tính chỉ số thực vật tăng cường EVI.
        evi: sentinel.expression('2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))', {
            'NIR': sentinel.select('B8'), 'RED': sentinel.select('B4'), 'BLUE': sentinel.select('B2')
        }).rename('EVI'),
        // Tính chỉ số thực vật điều chỉnh đất SAVI.
        savi: sentinel.expression('((NIR - RED) * (1.5)) / (NIR + RED + 0.5)', {
            'NIR': sentinel.select('B8'), 'RED': sentinel.select('B4')
        }).rename('SAVI'),
        // Tính chỉ số cháy chuẩn hóa NBR.
        nbr: sentinel.normalizedDifference(["B8", "B12"]).rename("NBR"),
        // Tính chỉ số độ ẩm chuẩn hóa NDMI.
        ndmi: sentinel.normalizedDifference(["B11", "B8"]).rename("NDMI")
    };
}

/**
 * Xử lý các nguồn dữ liệu môi trường bao gồm nhiệt độ, DEM, lượng mưa và gió.
 * Tính toán chỉ số VCI và TCI sử dụng NDVI được truyền vào.
 * @param {ee.Image} ndvi - Ảnh NDVI, được sử dụng để tính toán VCI.
 * @return {object} Đối tượng chứa các lớp dữ liệu môi trường đã xử lý.
 */
function processEnvironmentalData(ndvi) {
    // Tải dữ liệu nhiệt độ bề mặt đất (LST) từ MODIS.
    var tempCollection = ee.ImageCollection("MODIS/061/MOD11A2")
        .filterBounds(gia_lai) // Lọc theo vùng nghiên cứu.
        .filterDate(startDate, endDate) // Lọc theo khoảng thời gian.
        .select("LST_Day_1km"); // Chọn kênh nhiệt độ ban ngày.

    // Tính nhiệt độ trung bình, chuyển đổi từ Kelvin sang Celsius và cắt theo vùng nghiên cứu.
    // Đồng bộ hóa độ phân giải không gian (1000m) với các sản phẩm MODIS khác.
    var temperature = tempCollection.mean()
        .multiply(0.02).subtract(273.15) // Áp dụng hệ số tỷ lệ và hiệu chỉnh nhiệt độ.
        .rename("Temperature")
        .clip(gia_lai)
        .reproject({ crs: 'EPSG:4326', scale: 1000 }); // Chiếu lại về hệ tọa độ WGS84, độ phân giải 1km.

    // Tính giá trị NDVI tối thiểu và tối đa trong vùng nghiên cứu để tính chỉ số VCI.
    var ndviStats = ndvi.reduceRegion({
        reducer: ee.Reducer.minMax(),
        geometry: gia_lai.geometry(),
        scale: 30, // Độ phân giải của NDVI (Sentinel-2).
        maxPixels: 1e9,
        bestEffort: true // Sử dụng để tối ưu hóa tính toán khi xử lý vùng rộng lớn.
    });

    // Tạo ảnh hằng số cho giá trị NDVI tối thiểu và tối đa.
    var ndviMin = ee.Image.constant(ndviStats.get("NDVI_min"));
    var ndviMax = ee.Image.constant(ndviStats.get("NDVI_max"));

    // Tính chỉ số điều kiện thực vật (VCI).
    var vci = ndvi.subtract(ndviMin)
        .divide(ndviMax.subtract(ndviMin))
        .multiply(100).rename("VCI").clip(gia_lai);

    // Tính giá trị LST tối thiểu và tối đa từ bộ dữ liệu MODIS để tính TCI.
    var tempStats = tempCollection.reduce(ee.Reducer.minMax()); // Tính giá trị min/max từ bộ dữ liệu.
    // Chuyển đổi giá trị LST từ Kelvin sang Celsius.
    var lstMin = ee.Image(tempStats.select('LST_Day_1km_min')).multiply(0.02).subtract(273.15);
    var lstMax = ee.Image(tempStats.select('LST_Day_1km_max')).multiply(0.02).subtract(273.15);

    // Tính chỉ số điều kiện nhiệt độ (TCI).
    // Đồng bộ hóa độ phân giải không gian (1000m).
    var tci = lstMax.subtract(temperature)
        .divide(lstMax.subtract(lstMin))
        .multiply(100)
        .rename("TCI")
        .clip(gia_lai)
        .reproject({ crs: 'EPSG:4326', scale: 1000 });

    // Tải dữ liệu mô hình số độ cao (DEM) từ SRTM.
    var dem = ee.Image("USGS/SRTMGL1_003").rename("DEM").clip(gia_lai);
    // Tính toán các thông số địa hình (độ dốc, hướng dốc) từ DEM.
    var terrain = ee.Terrain.products(dem);

    // Tải dữ liệu lượng mưa hàng ngày từ CHIRPS.
    var precipitation = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterBounds(gia_lai) // Lọc theo vùng nghiên cứu.
        .filterDate(startDate, endDate) // Lọc theo khoảng thời gian.
        .mean() // Tính lượng mưa trung bình trong khoảng thời gian.
        .select("precipitation")
        .clip(gia_lai);

    // Tải dữ liệu gió tổng hợp hàng ngày từ ERA5 Land.
    var wind = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
        .filterBounds(gia_lai) // Lọc theo vùng nghiên cứu.
        .filterDate(startDate, endDate) // Lọc theo khoảng thời gian.
        .select(["u_component_of_wind_10m", "v_component_of_wind_10m"]) // Chọn thành phần gió U và V.
        .mean() // Tính giá trị trung bình của thành phần gió.
        .clip(gia_lai);

    // Trả về đối tượng chứa các lớp dữ liệu môi trường đã xử lý.
    return {
        temperature: temperature,
        vci: vci,
        tci: tci,
        dem: dem,
        slope: terrain.select("slope").rename("Slope").clip(gia_lai),
        aspect: terrain.select("aspect").rename("Aspect").clip(gia_lai),
        precipitation: precipitation,
        // Tính tốc độ gió từ các thành phần U và V.
        windSpeed: wind.expression(
            'sqrt(u*u + v*v)', {
            'u': wind.select('u_component_of_wind_10m'),
            'v': wind.select('v_component_of_wind_10m')
        }
        ).rename("WindSpeed").clip(gia_lai)
    };
}

/**
 * Huấn luyện mô hình Random Forest và Gradient Tree Boosting, đánh giá hiệu suất,
 * và tạo bản đồ nguy cơ cháy rừng.
 * @param {object} allData - Đối tượng chứa tất cả dữ liệu ảnh đã xử lý (chỉ số Sentinel, dữ liệu môi trường).
 * @param {ee.List} bands - Danh sách các kênh dữ liệu sử dụng làm biến dự đoán trong mô hình.
 * @return {object} Đối tượng chứa kết quả mô hình, bao gồm bản đồ nguy cơ và các chỉ số đánh giá.
 */
function trainAndEvaluateModels(allData, bands) {
    // Tải dữ liệu cháy chủ động từ MODIS để tạo nhãn cháy (dữ liệu thực tế).
    // Các giá trị FireMask > 6 (mức độ tin cậy danh nghĩa và cao) được coi là cháy.
    // Đồng bộ hóa độ phân giải không gian (500m) phù hợp với dữ liệu MODIS.
    var fireLabel = ee.ImageCollection("MODIS/061/MOD14A1")
        .filterBounds(gia_lai) // Lọc theo vùng nghiên cứu.
        .filterDate(startDate, endDate) // Lọc theo khoảng thời gian.
        .select("FireMask")
        .max() // Lấy giá trị phát hiện cháy tối đa trong khoảng thời gian.
        .gt(6) // Điểm ảnh có FireMask > 6 được gán nhãn là cháy (1), còn lại là không cháy (0).
        .rename("Fire_Label")
        .clip(gia_lai)
        .reproject({ crs: 'EPSG:4326', scale: 500 }); // Chiếu lại về hệ tọa độ WGS84, độ phân giải 500m.

    // Kết hợp tất cả các kênh dự đoán và nhãn cháy thành một ảnh đa kênh để lấy mẫu.
    // Đảm bảo nhất quán trong cách đặt tên các kênh dữ liệu.
    var featuresForSampling = ee.Image.cat([
        allData.ndvi, allData.ndwi, allData.lswi, allData.evi, allData.savi,
        allData.nbr, allData.ndmi, allData.temperature, allData.vci, allData.tci,
        allData.slope, allData.aspect,
        allData.precipitation.rename("Precipitation"), // Đảm bảo tên nhất quán.
        allData.windSpeed, allData.dem, fireLabel
    ]).select(bands.cat(["Fire_Label"])); // Chỉ chọn các kênh được chỉ định và nhãn.

    // Thực hiện lấy mẫu phân tầng để tạo tập dữ liệu huấn luyện và kiểm thử.
    // Phương pháp lấy mẫu phân tầng đảm bảo sự cân bằng giữa các lớp cháy và không cháy.
    var samples = featuresForSampling.stratifiedSample({
        numPoints: 1000, // Tổng số điểm lấy mẫu.
        classBand: "Fire_Label", // Kênh để phân tầng.
        region: gia_lai.geometry(), // Vùng lấy mẫu.
        scale: 500, // Độ phân giải lấy mẫu, cần tương thích với độ phân giải thô nhất hoặc độ phân giải mục tiêu.
        seed: 42, // Giá trị seed để đảm bảo tính tái lập.
        geometries: true, // Bao gồm thông tin hình học của các điểm lấy mẫu.
        dropNulls: true // Loại bỏ các điểm có giá trị null trong bất kỳ kênh nào.
    });
    // Lọc bổ sung để đảm bảo không có giá trị null trong các kênh dự đoán.
    samples = samples.filter(ee.Filter.notNull(bands));

    // Chia tập dữ liệu thành tập huấn luyện và tập kiểm thử (70% huấn luyện, 30% kiểm thử).
    var split = 0.7;
    samples = samples.randomColumn('random', 42); // Thêm cột giá trị ngẫu nhiên để phân chia.
    var training = samples.filter(ee.Filter.lt('random', split));
    var testing = samples.filter(ee.Filter.gte('random', split));

    // Thiết lập tham số cho mô hình Random Forest (RF).
    var rfParams = {
        numberOfTrees: 100,       // Số lượng cây quyết định trong rừng.
        minLeafPopulation: 5,     // Số lượng mẫu tối thiểu trong nút lá.
        bagFraction: 0.7,         // Tỷ lệ dữ liệu đầu vào để lấy mẫu có hoàn lại cho mỗi cây.
        seed: 42                  // Giá trị seed để đảm bảo tính tái lập.
    };

    // Thiết lập tham số cho mô hình Gradient Tree Boosting (GTB).
    var gtbParams = {
        numberOfTrees: 100,       // Số lượng cây quyết định.
        shrinkage: 0.05,          // Tốc độ học.
        samplingRate: 0.7,        // Tỷ lệ lấy mẫu con của dữ liệu đầu vào.
        maxNodes: 10,             // Số lượng nút tối đa cho mỗi cây.
        seed: 42                  // Giá trị seed để đảm bảo tính tái lập.
    };

    // Huấn luyện mô hình RF và GTB để đánh giá độ chính xác (chế độ đầu ra: CLASSIFICATION).
    var rfClassifierForAccuracy = ee.Classifier.smileRandomForest(rfParams).train(training, "Fire_Label", bands);
    var gtbClassifierForAccuracy = ee.Classifier.smileGradientTreeBoost(gtbParams).train(training, "Fire_Label", bands);

    // Huấn luyện mô hình RF và GTB để tạo đầu ra xác suất (chế độ đầu ra: PROBABILITY).
    var rfClassifierForProba = ee.Classifier.smileRandomForest(rfParams).setOutputMode('PROBABILITY').train(training, "Fire_Label", bands);
    var gtbClassifierForProba = ee.Classifier.smileGradientTreeBoost(gtbParams).setOutputMode('PROBABILITY').train(training, "Fire_Label", bands);

    // Xác định phép chiếu và độ phân giải không gian cho bản đồ phân loại cuối cùng.
    var targetProjection = allData.ndvi.projection(); // Sử dụng phép chiếu của NDVI làm tham chiếu.
    var targetScale = 30; // Độ phân giải mục tiêu 30m (độ phân giải Sentinel-2).

    // Kết hợp tất cả các kênh dự đoán cho việc phân loại bản đồ.
    var predictorsStackForMap = ee.Image.cat([
        allData.ndvi, allData.ndwi, allData.lswi, allData.evi, allData.savi,
        allData.nbr, allData.ndmi, allData.temperature, allData.vci, allData.tci,
        allData.slope, allData.aspect,
        allData.precipitation.rename("Precipitation"), // Đảm bảo tên nhất quán.
        allData.windSpeed, allData.dem
    ]).select(bands); // Chỉ chọn các kênh dự đoán.

    // Lấy mẫu lại và đồng bộ hóa độ phân giải không gian của tất cả các đặc trưng đầu vào.
    // Đảm bảo tất cả các đặc trưng có cùng thuộc tính không gian trước khi phân loại.
    var inputFeaturesForMapClassification = predictorsStackForMap
        .resample('bilinear') // Phương pháp lấy mẫu lại sử dụng nội suy song tuyến tính.
        .reproject({          // Chiếu lại về hệ tọa độ và độ phân giải mục tiêu.
            crs: targetProjection,
            scale: targetScale
        });

    // Phân loại dữ liệu đầu vào để tạo bản đồ xác suất cháy.
    // Kênh 'classification' từ chế độ PROBABILITY chứa xác suất của lớp dương (cháy).
    var rfProbability = inputFeaturesForMapClassification.classify(rfClassifierForProba).select('classification').rename("RF_Probability").clip(gia_lai);
    var gtbProbability = inputFeaturesForMapClassification.classify(gtbClassifierForProba).select('classification').rename("GTB_Probability").clip(gia_lai);

    // Chuyển đổi bản đồ xác suất thành các cấp độ nguy cơ rời rạc (1 đến 5).
    // Xác định ngưỡng để phân loại mức độ nguy cơ.
    var rfRiskLevels = rfProbability.expression(
        "(P <= 0.2) ? 1 : (P <= 0.4) ? 2 : (P <= 0.6) ? 3 : (P <= 0.8) ? 4 : 5", { P: rfProbability }
    ).rename("RF_Risk_Levels").clip(gia_lai);

    var gtbRiskLevels = gtbProbability.expression(
        "(P <= 0.2) ? 1 : (P <= 0.4) ? 2 : (P <= 0.6) ? 3 : (P <= 0.8) ? 4 : 5", { P: gtbProbability }
    ).rename("GTB_Risk_Levels").clip(gia_lai);

    // Xuất kết quả phân tích và đánh giá
    return {
        features: featuresForSampling, // Ảnh đa kênh được sử dụng để lấy mẫu.
        trainingData: training, // FeatureCollection cho huấn luyện mô hình và tính toán độ quan trọng của đặc trưng
        inputFeaturesForClassification: inputFeaturesForMapClassification, // Đặc trưng đầu vào cho phân loại bản đồ.
        rfRiskLevels: rfRiskLevels,   // Bản đồ cấp độ nguy cơ từ mô hình Random Forest.
        gtbRiskLevels: gtbRiskLevels,   // Bản đồ cấp độ nguy cơ từ mô hình Gradient Tree Boosting.
        // Ma trận lỗi cho mô hình RF trên tập kiểm thử.
        rfAccuracyMatrix: testing.classify(rfClassifierForAccuracy).errorMatrix('Fire_Label', 'classification'),
        // Ma trận lỗi cho mô hình GTB trên tập kiểm thử.
        gtbAccuracyMatrix: testing.classify(gtbClassifierForAccuracy).errorMatrix('Fire_Label', 'classification'),
        trainingSize: training.size(), // Số lượng mẫu trong tập huấn luyện.
        testingSize: testing.size()    // Số lượng mẫu trong tập kiểm thử.
    };
}

/**
 * Tạo chú giải cho bản đồ kết quả.
 * @param {Array<string>} colors - Mảng mã màu cho các mục chú giải.
 * @param {Array<string>} labels - Mảng nhãn tương ứng với các màu.
 * @return {ui.Panel} Đối tượng Panel UI đại diện cho chú giải.
 */
function createLegend(colors, labels) {
    // Tạo tiêu đề cho chú giải.
    var legendTitle = ui.Label({
        value: 'Mức độ nguy cơ cháy', // Tiêu đề chú giải
        style: { fontWeight: 'bold', fontSize: '16px', margin: '0 0 4px 0', padding: '0' }
    });
    // Tạo panel chính cho chú giải.
    var legend = ui.Panel({
        style: {
            position: 'bottom-right', // Định vị chú giải ở góc dưới bên phải bản đồ.
            padding: '8px 15px',
            border: '1px solid black' // Thêm viền cho chú giải.
        }
    });
    legend.add(legendTitle); // Thêm tiêu đề vào chú giải.

    // Tạo các mục cho chú giải bằng cách lặp qua các màu và nhãn.
    for (var i = 0; i < colors.length; i++) {
        // Tạo ô màu cho mục chú giải hiện tại.
        var colorBox = ui.Label({
            style: {
                backgroundColor: colors[i], // Đặt màu nền.
                padding: '8px',
                margin: '0 0 4px 0',
                border: '1px solid grey' // Thêm viền cho ô màu.
            }
        });
        // Tạo nhãn cho mô tả của mục chú giải hiện tại.
        var description = ui.Label({
            value: labels[i],
            style: { margin: '0 0 4px 6px' } // Thêm lề trái cho văn bản.
        });
        // Tạo panel để chứa ô màu và mô tả theo bố cục ngang.
        var legendEntry = ui.Panel({
            widgets: [colorBox, description],
            layout: ui.Panel.Layout.Flow('horizontal')
        });
        legend.add(legendEntry); // Thêm mục vào chú giải.
    }
    return legend; // Trả về chú giải đã tạo.
}

/**
 * Xuất bản đồ nguy cơ cháy rừng sang Google Drive và hiển thị các lớp dữ liệu trên bản đồ.
 * In các chỉ số đánh giá mô hình ra bảng điều khiển.
 * @param {object} allData - Đối tượng chứa tất cả dữ liệu ảnh đã xử lý.
 * @param {object} modelResults - Đối tượng chứa kết quả từ việc huấn luyện và đánh giá mô hình.
 * @param {ee.List} bands - Danh sách các kênh dữ liệu sử dụng làm biến dự đoán trong mô hình.
 * @param {object} rfParams - Tham số cấu hình cho mô hình Random Forest.
 * @param {object} gtbParams - Tham số cấu hình cho mô hình Gradient Tree Boosting.
 */
function exportAndDisplayResults(allData, modelResults, bands, rfParams, gtbParams) {
    // Khởi tạo tham số mô hình mặc định nếu không được cung cấp
    if (!rfParams) {
        rfParams = {
            numberOfTrees: 100,
            minLeafPopulation: 5,
            bagFraction: 0.7,
            seed: 42
        };
    }

    if (!gtbParams) {
        gtbParams = {
            numberOfTrees: 100,
            shrinkage: 0.05,
            samplingRate: 0.7,
            maxNodes: 10,
            seed: 42
        };
    }

    // Xuất bản đồ nguy cơ 5 cấp độ của mô hình Random Forest sang Google Drive.
    Export.image.toDrive({
        image: modelResults.rfRiskLevels,
        description: 'GiaLai_RF_Risk_5Levels',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // Xuất bản đồ nguy cơ từ mô hình Gradient Tree Boosting để so sánh
    Export.image.toDrive({
        image: modelResults.gtbRiskLevels,
        description: 'GiaLai_GTB_Risk_5Levels',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // Xuất dữ liệu cháy thực tế
    Export.image.toDrive({
        image: modelResults.features.select('Fire_Label').float(),
        description: 'GiaLai_Actual_Fire',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // Xuất từng chỉ số riêng lẻ để phân tích chi tiết
    // NDVI - Chỉ số khác biệt thực vật
    Export.image.toDrive({
        image: allData.ndvi.float(),
        description: 'GiaLai_NDVI',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // NDWI - Chỉ số khác biệt nước
    Export.image.toDrive({
        image: allData.ndwi.float(),
        description: 'GiaLai_NDWI',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // LSWI - Chỉ số nước bề mặt đất
    Export.image.toDrive({
        image: allData.lswi.float(),
        description: 'GiaLai_LSWI',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // EVI - Chỉ số thực vật tăng cường
    Export.image.toDrive({
        image: allData.evi.float(),
        description: 'GiaLai_EVI',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // SAVI - Chỉ số thực vật điều chỉnh đất
    Export.image.toDrive({
        image: allData.savi.float(),
        description: 'GiaLai_SAVI',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // NBR - Chỉ số cháy chuẩn hóa
    Export.image.toDrive({
        image: allData.nbr.float(),
        description: 'GiaLai_NBR',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // NDMI - Chỉ số độ ẩm chuẩn hóa
    Export.image.toDrive({
        image: allData.ndmi.float(),
        description: 'GiaLai_NDMI',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // Nhiệt độ bề mặt đất
    Export.image.toDrive({
        image: allData.temperature.float(),
        description: 'GiaLai_Temperature',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 1000,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // VCI - Chỉ số điều kiện thực vật
    Export.image.toDrive({
        image: allData.vci.float(),
        description: 'GiaLai_VCI',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // TCI - Chỉ số điều kiện nhiệt độ
    Export.image.toDrive({
        image: allData.tci.float(),
        description: 'GiaLai_TCI',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 1000,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // DEM - Mô hình số độ cao
    Export.image.toDrive({
        image: allData.dem.float(),
        description: 'GiaLai_DEM',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // Slope - Độ dốc địa hình
    Export.image.toDrive({
        image: allData.slope.float(),
        description: 'GiaLai_Slope',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // Aspect - Hướng dốc địa hình
    Export.image.toDrive({
        image: allData.aspect.float(),
        description: 'GiaLai_Aspect',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // Precipitation - Lượng mưa
    Export.image.toDrive({
        image: allData.precipitation.float(),
        description: 'GiaLai_Precipitation',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 5000,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // WindSpeed - Tốc độ gió
    Export.image.toDrive({
        image: allData.windSpeed.float(),
        description: 'GiaLai_WindSpeed',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 9000,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // Xuất ảnh Sentinel-2 đã xử lý (cho việc hiển thị và minh họa)
    Export.image.toDrive({
        image: allData.sentinel.select(['B4', 'B3', 'B2']),
        description: 'GiaLai_Sentinel2_RGB',
        folder: 'GEE_Export_GiaLai_Fire',
        region: gia_lai.geometry(),
        scale: 100,
        crs: 'EPSG:4326',
        maxPixels: 1e13
    });

    // Tính toán độ quan trọng của đặc trưng từ mô hình Random Forest
    var rfClassifier = ee.Classifier.smileRandomForest(rfParams)
        .train(modelResults.trainingData, 'Fire_Label', bands);

    // Tính toán độ quan trọng của đặc trưng từ mô hình Gradient Tree Boosting
    var gtbClassifier = ee.Classifier.smileGradientTreeBoost(gtbParams)
        .train(modelResults.trainingData, 'Fire_Label', bands);

    // Xuất dữ liệu huấn luyện với tất cả các đặc trưng để phân tích độ quan trọng trong Python
    Export.table.toDrive({
        collection: modelResults.trainingData,
        description: 'GiaLai_Training_Data_For_Feature_Importance',
        folder: 'GEE_Export_GiaLai_Fire',
        fileFormat: 'CSV'
    });

    // Tạo FeatureCollection chứa tên các đặc trưng
    var featureNamesFC = ee.FeatureCollection(bands.map(function (band) {
        return ee.Feature(null, { 'feature_name': band });
    }));

    // Xuất danh sách tên các đặc trưng
    Export.table.toDrive({
        collection: featureNamesFC,
        description: 'GiaLai_Feature_Names',
        folder: 'GEE_Export_GiaLai_Fire',
        fileFormat: 'CSV'
    });

    // Thiết lập hiển thị bản đồ
    // Căn chỉnh vị trí bản đồ theo vùng nghiên cứu
    Map.centerObject(gia_lai, 9); // Mức độ thu phóng 9

    // Thêm các lớp dữ liệu khác nhau vào bản đồ. Hầu hết được thiết lập ban đầu là ẩn (false).
    Map.addLayer(allData.ndvi, VIS_PARAMS.ndvi, "NDVI", false);
    Map.addLayer(allData.ndwi, VIS_PARAMS.ndwi, "NDWI", false);
    Map.addLayer(allData.lswi, VIS_PARAMS.ndwi, "LSWI", false);
    Map.addLayer(allData.evi, VIS_PARAMS.ndvi, "EVI", false);
    Map.addLayer(allData.savi, VIS_PARAMS.ndvi, "SAVI", false);
    Map.addLayer(allData.nbr, VIS_PARAMS.ndvi, "NBR", false);
    Map.addLayer(allData.ndmi, VIS_PARAMS.ndwi, "NDMI", false);
    Map.addLayer(allData.temperature, VIS_PARAMS.temp, "Nhiệt độ (MODIS)", false);
    Map.addLayer(allData.vci, VIS_PARAMS.vci, "VCI", false);
    Map.addLayer(allData.tci, VIS_PARAMS.tci, "TCI", false);
    Map.addLayer(allData.dem, VIS_PARAMS.dem, "Địa hình DEM", false);
    Map.addLayer(allData.slope, VIS_PARAMS.slope, "Độ dốc", false);
    Map.addLayer(allData.aspect, { min: 0, max: 360, palette: ['#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928', '#000000'] }, "Hướng dốc", false);
    Map.addLayer(allData.precipitation, { min: 0, max: 15, palette: ['white', 'blue'] }, "Lượng mưa (CHIRPS)", false);
    Map.addLayer(allData.windSpeed, { min: 0, max: 10, palette: ['white', 'cyan'] }, "Tốc độ gió (ERA5)", false);
    Map.addLayer(modelResults.features.select('Fire_Label'), VIS_PARAMS.fire, "Nhãn cháy thực tế (MODIS)", false);
    Map.addLayer(modelResults.rfRiskLevels, VIS_PARAMS.prediction_5levels, "Dự đoán cháy 5 mức (RF)");
    Map.addLayer(modelResults.gtbRiskLevels, VIS_PARAMS.prediction_5levels, "Dự đoán cháy 5 mức (GTB)");

    // Thiết lập chú giải cho bản đồ nguy cơ cháy
    // Xác định màu sắc và nhãn tương ứng với các cấp độ nguy cơ
    var colors = VIS_PARAMS.prediction_5levels.palette;
    var labels = [
        '1: Thấp',            // Cấp độ nguy cơ thấp
        '2: Trung bình',      // Cấp độ nguy cơ trung bình
        '3: Cao',             // Cấp độ nguy cơ cao
        '4: Nguy hiểm',       // Cấp độ nguy cơ nguy hiểm
        '5: Cực kỳ nguy hiểm' // Cấp độ nguy cơ cực kỳ nguy hiểm
    ];
    // Tạo và thêm chú giải vào bản đồ.
    var legend = createLegend(colors, labels);
    Map.add(legend);

    // In kết quả đánh giá mô hình ra bảng điều khiển.
    print("Số điểm mẫu huấn luyện:", modelResults.trainingSize);
    print("Số điểm mẫu kiểm thử:", modelResults.testingSize);

    // Tính toán và hiển thị các chỉ số hiệu suất của mô hình Random Forest.
    var rfAccuracy = modelResults.rfAccuracyMatrix.accuracy();
    print("Ma trận lỗi Random Forest:", modelResults.rfAccuracyMatrix);
    print("Độ chính xác tổng thể (Overall Accuracy) RF:", rfAccuracy);

    // Tính toán hệ số Kappa cho mô hình RF
    var rfKappa = modelResults.rfAccuracyMatrix.kappa();
    print("Hệ số Kappa cho RF:", rfKappa);

    // Hiển thị ma trận lỗi cho mô hình GTB
    print("Ma trận lỗi Gradient Tree Boosting:", modelResults.gtbAccuracyMatrix);

    // Tính toán độ chính xác tổng thể cho mô hình GTB
    var gtbAccuracy = modelResults.gtbAccuracyMatrix.accuracy();
    print("Độ chính xác tổng thể (Overall Accuracy) GTB:", gtbAccuracy);

    // Tính toán hệ số Kappa cho mô hình GTB
    var gtbKappa = modelResults.gtbAccuracyMatrix.kappa();
    print("Hệ số Kappa cho GTB:", gtbKappa);

    // Xuất các chỉ số đánh giá mô hình để phân tích ngoại tuyến
    Export.table.toDrive({
        collection: ee.FeatureCollection([
            ee.Feature(null, {
                rf_accuracy: ee.Number(rfAccuracy).float(),
                rf_kappa: ee.Number(rfKappa).float(),
                gtb_accuracy: ee.Number(gtbAccuracy).float(),
                gtb_kappa: ee.Number(gtbKappa).float()
            })
        ]),
        description: 'GiaLai_Model_Evaluation_Metrics',
        folder: 'GEE_Export_GiaLai_Fire',
        fileFormat: 'CSV'
    });
}

/**
 * Hàm chính điều phối toàn bộ quy trình xử lý và phân tích.
 */
function main() {
    // Xác định danh sách các biến dự đoán sử dụng trong mô hình.
    // Các tên phải khớp với tên được gán khi tạo các đặc trưng tương ứng.
    var bands = ee.List([
        "NDVI", "NDWI", "LSWI", "EVI", "SAVI", "NBR", "NDMI",
        "Temperature", "VCI", "TCI", "Slope", "Aspect",
        "Precipitation", "WindSpeed", "DEM"
    ]);

    // Thiết lập tham số cho mô hình Random Forest (RF).
    var rfParams = {
        numberOfTrees: 100,       // Số lượng cây quyết định trong rừng.
        minLeafPopulation: 5,     // Số lượng mẫu tối thiểu trong nút lá.
        bagFraction: 0.7,         // Tỷ lệ dữ liệu lấy mẫu có hoàn lại cho mỗi cây.
        seed: 42                  // Giá trị seed để đảm bảo tính tái lập.
    };

    // Thiết lập tham số cho mô hình Gradient Tree Boosting (GTB).
    var gtbParams = {
        numberOfTrees: 100,       // Số lượng cây quyết định.
        shrinkage: 0.05,          // Tốc độ học.
        samplingRate: 0.7,        // Tỷ lệ lấy mẫu con của dữ liệu.
        maxNodes: 10,             // Số lượng nút tối đa cho mỗi cây.
        seed: 42                  // Giá trị seed để đảm bảo tính tái lập.
    };

    // Bước 1: Xử lý dữ liệu Sentinel-2 để tính toán các chỉ số thực vật.
    var sentinelData = processSentinel();

    // Bước 2: Xử lý dữ liệu môi trường (nhiệt độ, VCI, TCI, DEM, v.v.).
    // Sử dụng NDVI từ dữ liệu Sentinel để tính toán VCI.
    var envData = processEnvironmentalData(sentinelData.ndvi);

    // Bước 3: Tổng hợp tất cả dữ liệu đã xử lý vào một đối tượng.
    // Điều này giúp dễ dàng truyền dữ liệu giữa các hàm.
    var allData = {
        sentinel: sentinelData.sentinel,
        ndvi: sentinelData.ndvi,
        ndwi: sentinelData.ndwi,
        lswi: sentinelData.lswi,
        evi: sentinelData.evi,
        savi: sentinelData.savi,
        nbr: sentinelData.nbr,
        ndmi: sentinelData.ndmi,
        temperature: envData.temperature,
        vci: envData.vci,
        tci: envData.tci,
        dem: envData.dem,
        slope: envData.slope,
        aspect: envData.aspect,
        precipitation: envData.precipitation,
        windSpeed: envData.windSpeed
    };

    // Bước 4: Huấn luyện các mô hình học máy và đánh giá hiệu suất.
    var modelResults = trainAndEvaluateModels(allData, bands);

    // Bước 5: Xuất kết quả (bản đồ nguy cơ) và hiển thị trên giao diện.
    // Đồng thời, hiển thị các chỉ số đánh giá hiệu suất.
    exportAndDisplayResults(allData, modelResults, bands, rfParams, gtbParams);
}

// Thực thi hàm chính để bắt đầu quy trình phân tích.
main();