'use strict';

Object.defineProperty(exports, "__esModule", {
    value: true
});

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

var _react = require('react');

var React = _interopRequireWildcard(_react);

var _dateFns = require('date-fns');

function _interopRequireWildcard(obj) { if (obj && obj.__esModule) { return obj; } else { var newObj = {}; if (obj != null) { for (var key in obj) { if (Object.prototype.hasOwnProperty.call(obj, key)) newObj[key] = obj[key]; } } newObj.default = obj; return newObj; } }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

var _class = function (_React$Component) {
    _inherits(_class, _React$Component);

    function _class() {
        _classCallCheck(this, _class);

        var _this = _possibleConstructorReturn(this, (_class.__proto__ || Object.getPrototypeOf(_class)).call(this));

        _this.state = {
            currentMachine: 'all',
            currentSequence: 'all'
        };
        return _this;
    }

    _createClass(_class, [{
        key: 'filteredMachineSequencePairs',
        value: function filteredMachineSequencePairs() {
            var machineSequencePairs = this.props.machineSequencePairs;
            var _state = this.state,
                currentMachine = _state.currentMachine,
                currentSequence = _state.currentSequence;

            var filteredMachineSequencePairs = machineSequencePairs;
            if (currentMachine != 'all') {
                filteredMachineSequencePairs = filteredMachineSequencePairs.filter(function (pair) {
                    return pair.machine == currentMachine;
                });
            }
            if (currentSequence != 'all') {
                filteredMachineSequencePairs = filteredMachineSequencePairs.filter(function (pair) {
                    return pair.sequence == currentSequence;
                });
            }
            return filteredMachineSequencePairs;
        }
    }, {
        key: 'handleMachineChange',
        value: function handleMachineChange(event) {
            this.setState({ currentMachine: event.target.value });
        }
    }, {
        key: 'handleSequenceChange',
        value: function handleSequenceChange(event) {
            this.setState({ currentSequence: event.target.value });
        }
    }, {
        key: 'render',
        value: function render() {
            var _props = this.props,
                machines = _props.machines,
                sequences = _props.sequences;
            var _state2 = this.state,
                currentMachine = _state2.currentMachine,
                currentSequence = _state2.currentSequence;

            var filteredMachineSequencePairs = this.filteredMachineSequencePairs();
            return React.createElement("div", null, React.createElement("a", { href: "#" }, "Upload New Scan"), React.createElement("div", null, "Filter By", React.createElement("select", { value: currentMachine, onChange: this.handleMachineChange.bind(this) }, React.createElement("option", { value: "all" }, "All Machines"), machines.map(function (machine) {
                return React.createElement("option", { value: machine.pk, key: machine.pk }, machine.name);
            })), React.createElement("select", { value: currentSequence, onChange: this.handleSequenceChange.bind(this) }, React.createElement("option", { value: "all" }, "All Sequences"), sequences.map(function (sequence) {
                return React.createElement("option", { value: sequence.pk, key: sequence.pk }, sequence.name);
            }))), React.createElement("table", null, React.createElement("thead", null, React.createElement("tr", null, React.createElement("th", null, "Machine"), React.createElement("th", null, "Sequence"), React.createElement("th", null, "Date of Latest Scan"), React.createElement("th", null, "Latest Scan Within Tolerance?"), React.createElement("th", null, "Actions"))), React.createElement("tbody", null, filteredMachineSequencePairs.map(function (pair) {
                return React.createElement("tr", { key: pair.pk }, React.createElement("td", null, machines.find(function (machine) {
                    return machine.pk === pair.machine;
                }).name), React.createElement("td", null, sequences.find(function (sequence) {
                    return sequence.pk === pair.sequence;
                }).name), React.createElement("td", null, pair.latest_scan_date && (0, _dateFns.format)(new Date(pair.latest_scan_date), 'D MMM YYYY')), React.createElement("td", null, pair.latest_scan_within_tolerance !== null && (pair.latest_scan_within_tolerance ? React.createElement("i", { className: "fa fa-check", "aria-hidden": "true" }) : React.createElement("i", { className: "fa fa-times", "aria-hidden": "true" }))), React.createElement("td", null, React.createElement("a", { href: pair.detail_url }, "View Details")));
            }))));
        }
    }]);

    return _class;
}(React.Component);
//# sourceMappingURL=MachineSequenceTable.js.map


exports.default = _class;