
import React from 'react';
import styled from 'styled-components';

const ROW_INDICATORS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"];
const COL_INDICATORS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"];

const CELL_TYPE_OCEAN = 0;
const CELL_TYPE_PLAYER_ONE = 1;
const CELL_TYPE_PLAYER_TWO = 2;
const CELL_TYPE_UNKNOWN = 3;


const IMAGE_BASE = "/src/abacship/images";

class OceanCell extends React.PureComponent {
  render() {
    const { type } = this.props;
    switch (type) {
      case CELL_TYPE_OCEAN:
        return <img alt="Ocean" src={`${IMAGE_BASE}/ocean.jpg`} />

      case CELL_TYPE_PLAYER_ONE:
        return <img alt="Player One" src={`${IMAGE_BASE}/player-one.jpg`} />

      case CELL_TYPE_PLAYER_TWO:
        return <img alt="Player Two" src={`${IMAGE_BASE}/player-two.jpg`} />

      case CELL_TYPE_UNKNOWN:
        return <img alt="Unknown" src={`${IMAGE_BASE}/unknown.jpg`} />

      default:
        throw new Error(`Unknown cell type: ${type}`);
    }
  }
}


const InlineTable = styled.table`
  display: inline-table;
`;

export class OceanGrid extends React.PureComponent {
  render() {
    const { grid } = this.props;

    const headerColumns = [
      // First column is the corner, which does not need to say anything.
      <>&nbsp;</>,
    ];
    COL_INDICATORS.forEach(indicator => {
      headerColumns.push(indicator);
    });

    const rows = [headerColumns];
    ROW_INDICATORS.forEach(indicator => {
      const row = [indicator];
      // First row is the indicator row.
      const gridRowIndex = rows.length - 1;
      grid[gridRowIndex].forEach(gridCell => {
        row.push(<OceanCell type={gridCell} />);
      });
      rows.push(row);
    });

    return (
      <InlineTable>
        {rows.map((row, rowIdx) => (
          <tr key={rowIdx}>
            {row.map((cell, cellIdx) => <td key={cellIdx} align="center" valign="center">{cell}</td>)}
          </tr>
        ))}
      </InlineTable>
    );
  }
}



const CenteredDiv = styled.div`
  text-align: center;
`;

const CELL_TYPES = [CELL_TYPE_OCEAN, CELL_TYPE_PLAYER_ONE, CELL_TYPE_PLAYER_TWO, CELL_TYPE_UNKNOWN];
function randomCellType() {
  return CELL_TYPES[Math.floor(Math.random() * CELL_TYPES.length)];
}

export default class ABACShip extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      myGrid: null,
      opponentGrid: null,
    };
  }

  async getMyGrid() {
    return ROW_INDICATORS.map(() => COL_INDICATORS.map(() => randomCellType()));
  }

  async getOpponentGrid() {
    return ROW_INDICATORS.map(() => COL_INDICATORS.map(() => randomCellType()));
  }

  async componentDidMount() {
    const stateUpdate = {};
    stateUpdate.myGrid = await this.getMyGrid();
    stateUpdate.opponentGrid = await this.getOpponentGrid();
    this.setState(stateUpdate);
  }

  render() {
    const { myGrid, opponentGrid } = this.state;

    if (myGrid === null || opponentGrid === null) {
      return null;
    }

    return (
      <CenteredDiv>
        <img alt="ABACShip" src={`${IMAGE_BASE}/abacship.jpg`} />
        <CenteredDiv>
          <OceanGrid grid={myGrid} />
        </CenteredDiv>
        <CenteredDiv>
          <OceanGrid grid={opponentGrid} />
        </CenteredDiv>
      </CenteredDiv>
    );
  }
}
