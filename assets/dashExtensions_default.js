window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, context) {
            const {
                classes,
                colorscale,
                style,
                colorProp
            } = context.hideout;
            const value = feature.properties[colorProp];

            if (value === 1000) {
                style.fillColor = colorscale[colorscale.length - 1]; // Use last color (dark grey) for missing data
                return style;
            }

            if (value < 0) { // Handle negative values
                for (let i = 0; i < 3; ++i) { // 3 is the number of negative classes
                    if (value <= classes[i]) {
                        style.fillColor = colorscale[i];
                        break;
                    }
                }
            } else { // Handle zero and positive values
                for (let i = 3; i < classes.length - 1; ++i) { // Start from first positive class
                    if (value <= classes[i]) {
                        style.fillColor = colorscale[i];
                        break;
                    }
                }
                // If no class matched (value is greater than all class boundaries)
                if (value > classes[classes.length - 2]) {
                    style.fillColor = colorscale[classes.length - 2]; // Use the last color before grey
                }
            }
            return style;
        }
    }
});