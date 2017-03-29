import * as React from 'react';
import { format } from 'date-fns';
export default class extends React.Component {
    constructor() {
        super();
        this.state = {
            currentMachine: 'all',
            currentSequence: 'all',
        };
    }
    filteredMachineSequencePairs() {
        const { machineSequencePairs } = this.props;
        const { currentMachine, currentSequence } = this.state;
        let filteredMachineSequencePairs = machineSequencePairs;
        if (currentMachine != 'all') {
            filteredMachineSequencePairs = filteredMachineSequencePairs.filter((pair) => pair.machine == currentMachine);
        }
        if (currentSequence != 'all') {
            filteredMachineSequencePairs = filteredMachineSequencePairs.filter((pair) => pair.sequence == currentSequence);
        }
        return filteredMachineSequencePairs;
    }
    handleMachineChange(event) {
        this.setState({ currentMachine: event.target.value });
    }
    handleSequenceChange(event) {
        this.setState({ currentSequence: event.target.value });
    }
    render() {
        const { machines, sequences } = this.props;
        const { currentMachine, currentSequence } = this.state;
        const filteredMachineSequencePairs = this.filteredMachineSequencePairs();
        return (React.createElement("div", null,
            React.createElement("a", { href: "#" }, "Upload New Scan"),
            React.createElement("div", null,
                "Filter By",
                React.createElement("select", { value: currentMachine, onChange: this.handleMachineChange.bind(this) },
                    React.createElement("option", { value: "all" }, "All Machines"),
                    machines.map((machine) => React.createElement("option", { value: machine.pk, key: machine.pk }, machine.name))),
                React.createElement("select", { value: currentSequence, onChange: this.handleSequenceChange.bind(this) },
                    React.createElement("option", { value: "all" }, "All Sequences"),
                    sequences.map((sequence) => React.createElement("option", { value: sequence.pk, key: sequence.pk }, sequence.name)))),
            React.createElement("table", null,
                React.createElement("thead", null,
                    React.createElement("tr", null,
                        React.createElement("th", null, "Machine"),
                        React.createElement("th", null, "Sequence"),
                        React.createElement("th", null, "Date of Latest Scan"),
                        React.createElement("th", null, "Latest Scan Within Tolerance?"),
                        React.createElement("th", null, "Actions"))),
                React.createElement("tbody", null, filteredMachineSequencePairs.map((pair) => (React.createElement("tr", { key: pair.pk },
                    React.createElement("td", null, machines.find((machine) => machine.pk === pair.machine).name),
                    React.createElement("td", null, sequences.find((sequence) => sequence.pk === pair.sequence).name),
                    React.createElement("td", null, pair.latest_scan_date && format(new Date(pair.latest_scan_date), 'D MMM YYYY')),
                    React.createElement("td", null, pair.latest_scan_within_tolerance !== null && (pair.latest_scan_within_tolerance ? React.createElement("i", { className: "fa fa-check", "aria-hidden": "true" }) : React.createElement("i", { className: "fa fa-times", "aria-hidden": "true" }))),
                    React.createElement("td", null,
                        React.createElement("a", { href: pair.detail_url }, "View Details")))))))));
    }
}
//# sourceMappingURL=MachineSequenceTable.js.map