//------------------------------------//
//  Tải dữ liệu khu vực Gia Lai
//------------------------------------//
var gia_lai = ee.FeatureCollection("projects/ee-bonglantrungmuoi/assets/gia_lai");
var startDate = "2024-12-01";
var endDate = "2025-04-30";

Map.centerObject(gia_lai, 8);

//------------------------------------//
//  Ảnh Sentinel-2 thực màu
//------------------------------------//
function maskClouds(image) {
    var cloudProb = image.select("MSK_CLDPRB");
    return image.updateMask(cloudProb.lt(30));
}

var s2Collection = ee.ImageCollection("COPERNICUS/S2_SR")
    .filterBounds(gia_lai)
    .filterDate(startDate, endDate)
    .filterMetadata("CLOUDY_PIXEL_PERCENTAGE", "less_than", 10)
    .map(maskClouds);

// Ảnh thực màu RGB (chưa clip) - giữ lại cho xuất raw
var rgbComposite = s2Collection
    .select(["B4", "B3", "B2"])
    .median();

// Tạo ảnh nền trắng cho toàn bộ khu vực
var whiteBackground = ee.Image(1).visualize({ palette: ['ffffff'] });

// Tạo ảnh true color
var trueColorImage = rgbComposite.visualize({
    min: 1000,
    max: 2500,
    bands: ["B4", "B3", "B2"]
});

// Clip ảnh theo ranh giới Gia Lai
var trueColorClipped = trueColorImage.clipToCollection(gia_lai);

// Bước 1: Kết hợp nền trắng với ảnh true color đã được clip
var compositeWithWhite = ee.ImageCollection([
    whiteBackground,
    trueColorClipped
]).mosaic();

// Bước 2: Tạo ranh giới đen cho tỉnh Gia Lai 
var outline = ee.Image().byte()
    .paint({
        featureCollection: gia_lai,
        color: 1,
        width: 2.0
    })
    .visualize({ palette: ['000000'] });

// Bước 3: Kết hợp ảnh đã có với đường viền đen
var finalVisual = ee.ImageCollection([
    compositeWithWhite,
    outline
]).mosaic();

// Hiển thị ảnh cuối cùng
Map.addLayer(finalVisual, {}, "Ảnh thực màu (Sentinel-2)");

//------------------------------------//
//  Xuất ảnh (Export)
//------------------------------------//
function exportImage(image, desc, prefix) {
    Export.image.toDrive({
        image: image,
        description: desc,
        folder: "GEE_Biomass_Export",
        fileNamePrefix: prefix,
        region: gia_lai.geometry().buffer(0.1), // Mở rộng khu vực để đảm bảo có nền trắng
        scale: 100,
        crs: "EPSG:4326",
        maxPixels: 1e13
    });
}

// Xuất ảnh thực màu với nền trắng và đường viền đen
exportImage(finalVisual, "GiaLai_TrueColor_S2_WhiteBG", "GiaLai_TrueColor_WhiteBG");

// Xuất ảnh raw bands cho phân tích (không visualize)
exportImage(rgbComposite.clip(gia_lai), "GiaLai_TrueColor_S2_Raw", "GiaLai_TrueColor_Raw");
