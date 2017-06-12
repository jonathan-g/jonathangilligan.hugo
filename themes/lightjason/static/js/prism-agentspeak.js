Prism.languages.agentspeak = Prism.languages.extend('clike', {
    'constant': /\b(pi|euler|gravity|avogadro|boltzmann|electron|proton|neutron|lightspeed|infinity)\b/,
    'class-name': null,
    'keyword': /\b([a-z][\w|\-|/]*)\b/,
    'variable': /\b([A-Z][\w|\-|/]*)\b/,
    'operator': /[~=><:\-+?@;|!{1,2}$.]+/,
    'boolean': /\b(true|success|false|fail)\b/
} );
