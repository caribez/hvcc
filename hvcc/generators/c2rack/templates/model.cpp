#include "plugin.hpp"

struct Heavy{{name}}Module : Module {
    enum ParamIds {
    {% for k, v in receivers %}
        HV_{{v.display|upper}}_PARAM,{% endfor %}
        NUM_PARAMS
    };
    enum InputIds {
    {% for param, name, typ, namehash, minvalue, maxvalue, defvalue in jdata if typ == 'RECV' %}
        HV_{{param|upper}}_INPUT,{% endfor %}
        NUM_INPUTS
    };
    enum OutputIds {
    {% for param, name, typ, namehash, minvalue, maxvalue, defvalue in jdata if typ == 'SEND' %}
        HV_{{param|upper}}_OUTPUT,{% endfor %}
        NUM_OUTPUTS
    };
    enum LightIds {
        NUM_LIGHTS
    };

    Heavy{{name}}Module() {
        config(NUM_PARAMS, NUM_INPUTS, NUM_OUTPUTS, NUM_LIGHTS);
    }
};

// struct Heavy{{name}}Image : Widget {
//     int imageId = -2;
//     int imageWidth = 0;
//     int imageHeight = 0;
//     bool hasModule;

//     Heavy{{name}}Image(const math::Vec& size, const bool hasModule) {
//         box.size = size;
//         this->hasModule = hasModule;
//     }

//     void draw(const DrawArgs& args) override
//     {
//         if (imageId == -2)
//         {
//             imageId = nvgCreateImage(args.vg, asset::plugin(pluginInstance, "res/Miku/Miku.png").c_str(), 0);

//             if (imageId != -1)
//                 nvgImageSize(args.vg, imageId, &imageWidth, &imageHeight);
//         }

//         if (imageId != -1 && imageWidth != 0 && imageHeight != 0)
//         {
//             const float pixelRatio = hasModule ? APP->window->pixelRatio : 1.0f;
//             const float boxscale = std::min(box.size.x / imageWidth, box.size.y / imageHeight);
//             const float imgHeight = (imageHeight / pixelRatio) * boxscale;
//             nvgBeginPath(args.vg);
//             nvgRect(args.vg, 0, 0, box.size.x, box.size.y);
//             nvgFillPaint(args.vg, nvgImagePattern(args.vg,
//                                                   0,
//                                                   (box.size.y / pixelRatio) * 0.5f - imgHeight * 0.5f,
//                                                   box.size.x / pixelRatio,
//                                                   imgHeight, 0, imageId, 1.0f));
//             nvgFill(args.vg);
//         }
//     }
// };

// struct Heavy{{name}}Widget : ModuleWidget {
//     Heavy{{name}}Widget(Heavy{{name}}Module* const module) {
//         setModule(module);
//         setPanel(APP->window->loadSvg(asset::plugin(pluginInstance, "res/{{name}}.svg")));

//         addChild(createWidget<ScrewBlack>(Vec(RACK_GRID_WIDTH, 0)));
//         addChild(createWidget<ScrewBlack>(Vec(box.size.x - 2 * RACK_GRID_WIDTH, 0)));
//         addChild(createWidget<ScrewBlack>(Vec(RACK_GRID_WIDTH, RACK_GRID_HEIGHT - RACK_GRID_WIDTH)));
//         addChild(createWidget<ScrewBlack>(Vec(box.size.x - 2 * RACK_GRID_WIDTH, RACK_GRID_HEIGHT - RACK_GRID_WIDTH)));

//         FramebufferWidget* const fbWidget = new FramebufferWidget;
//         fbWidget->oversample = 2.0;
//         fbWidget->addChild(new Heavy{{name}}Image(box.size, module != nullptr));
//         addChild(fbWidget);
//     }

//     void draw(const DrawArgs& args) override
//     {
//         nvgBeginPath(args.vg);
//         nvgRect(args.vg, 0, 0, box.size.x, box.size.y);
//         nvgFillPaint(args.vg, nvgLinearGradient(args.vg, 0, 0, 0, box.size.y,
//                                                 nvgRGB(0x18, 0x19, 0x19), nvgRGB(0x21, 0x22, 0x22)));
//         nvgFill(args.vg);

//         ModuleWidget::draw(args);
//     }
// };

Model* modelHeavy{{name}} = createModel<Heavy{{name}}Module, Heavy{{name}}Widget>("{{name}}");
