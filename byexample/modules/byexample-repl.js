const _repl_module = require('repl')
// other interesting flags: useGlobal, ignoreUndefined, replMode
var _repl = _repl_module.start({prompt: 'node > ',
                                useColors: false,
                                terminal: false,
                                ignoreUndefined: true})
