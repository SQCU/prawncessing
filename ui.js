// ui.js - Functions for dynamically generating the application's UI

/**
 * Creates a control group (label + input) and appends it to the controls container.
 * @param {p5.p5Instance} p5 - The p5.js instance.
 * @param {object} config - Configuration object for the control.
 * @param {object} controlsRegistry - The object to store the created control in.
 */
function createControlGroup(p5, config, controlsRegistry) {
    const container = p5.createDiv().addClass('control-group').parent('controls');
    p5.createSpan(config.label).parent(container);
    let control;
    switch(config.type) {
        case 'select':
            control = p5.createSelect().parent(container);
            config.options.forEach(opt => control.option(opt));
            break;
        case 'slider':
            control = p5.createSlider(config.min, config.max, config.default, config.step).parent(container);
            break;
        case 'checkbox':
            control = p5.createCheckbox('', config.default).parent(container);
            break;
    }
    controlsRegistry[config.id] = control;
}

/**
 * Creates a module's info card (header, stats) and appends it to the pipeline.
 * THIS FUNCTION DOES NOT CREATE CANVASES.
 * @param {p5.p5Instance} p5 - The p5.js instance.
 * @param {object} config - Configuration object for the module.
 * @param {object} appState - The main application state object.
 * @param {string} parentId - The ID of the DOM element to append this card to.
 */
function createModule(p5, config, appState, parentId) {
    const container = p5.createDiv().addClass('module-container').parent(parentId);
    const header = p5.createDiv().addClass('module-header').parent(container);
    p5.createSpan(config.title).parent(header);
    if(config.toggleId) {
        const toggle = p5.createCheckbox('', true).parent(header);
        toggle.changed(() => appState.toggles[config.toggleId] = toggle.checked());
    }
    p5.createDiv('').id(`stats-${config.id}`).addClass('log-card' + (config.isGlobal ? ' global-log-card' : '')).parent(container);
}