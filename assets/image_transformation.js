if (typeof window.dash_clientside === 'undefined') {
    window.dash_clientside = {};
}

if (typeof window.dash_clientside.clientside === 'undefined') {
    window.dash_clientside.clientside = {};
}

window.dash_clientside.clientside.transform_image = function(logToggle, current_data, data) {
    console.log("Received logToggle:", logToggle); // Check logToggle value
    console.log("Received src:", data); // Check src value
    src = data;
    // If logToggle is false or src is not provided, return the original src
    if (!logToggle || !src || (logToggle && src != current_data)) {
        console.log("Returning original image without transformation.");
        return Promise.resolve(src);
    }

    return new Promise(function(resolve, reject) {
        // Create an Image element
        var image = new Image();
        image.onload = function() {
            // If logToggle is true, proceed with the transformation
            var canvas = document.createElement('canvas');
            canvas.width = image.width;
            canvas.height = image.height;
            var ctx = canvas.getContext('2d');

            ctx.drawImage(image, 0, 0, image.width, image.height);
            var imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            var data = imageData.data;

            // Apply log(1+x) transformation to each pixel
            for (var i = 0; i < data.length; i += 4) {
                data[i] = (255 / Math.log(256)) * Math.log1p(data[i]);       // Red
                data[i + 1] = (255 / Math.log(256)) * Math.log1p(data[i + 1]); // Green
                data[i + 2] = (255 / Math.log(256)) * Math.log1p(data[i + 2]); // Blue
                // Alpha channel remains unchanged
            }

            ctx.putImageData(imageData, 0, 0);
            resolve(canvas.toDataURL()); // Convert the canvas back to a base64 URL
        };
        image.onerror = function() {
            console.error("Failed to load image");
            reject(new Error('Failed to load image'));
        };
        image.src = src;
    });
}
