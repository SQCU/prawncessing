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
 * Creates a processing module (header, stats card, canvas panel) and appends it to the pipeline.
 * @param {p5.p5Instance} p5 - The p5.js instance.
 * @param {object} config - Configuration object for the module.
 * @param {object} appState - The main application state object.
 */
function createModule(p5, config, appState) {
    const container = p5.createDiv().addClass('module-container').parent('pipeline-container');
    const header = p5.createDiv().addClass('module-header').parent(container);
    p5.createSpan(config.title).parent(header);
    if(config.toggleId) {
        const toggle = p5.createCheckbox('', true).parent(header);
        toggle.changed(() => appState.toggles[config.toggleId] = toggle.checked());
    }
    p5.createDiv('').id(`stats-${config.id}`).addClass('log-card' + (config.isGlobal ? ' global-log-card' : '')).parent(container);
    
    // FIX: The canvas wrapper div MUST be parented to its own module's container.
    // The .parent(container) call at the end of this line is the crucial fix.
    // Without it, the div is created but never attached to the page.
    if(config.hasCanvas) {
        p5.createDiv('').id(`panel-${config.id}`).addClass('canvas-wrapper').parent(container);
    }
}