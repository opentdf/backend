
import React from 'react';
import styled from 'styled-components';

const ROW_INDICATORS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"];
const COL_INDICATORS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"];

const CELL_TYPE_OCEAN = 0;
const CELL_TYPE_PLAYER_ONE = 1;
const CELL_TYPE_PLAYER_TWO = 2;
const CELL_TYPE_UNKNOWN = 3;


const IMAGE_BASE = "/src/abacship/images";

const BlockImage = styled.img`
  display: block;
`;

class OceanCell extends React.PureComponent {
  render() {
    const { type } = this.props;
    switch (type) {
      case CELL_TYPE_OCEAN:
        return <BlockImage alt="Ocean" src={`${IMAGE_BASE}/ocean.jpg`} />

      case CELL_TYPE_PLAYER_ONE:
        return <BlockImage alt="Player One" src={`${IMAGE_BASE}/player-one.jpg`} />

      case CELL_TYPE_PLAYER_TWO:
        return <BlockImage alt="Player Two" src={`${IMAGE_BASE}/player-two.jpg`} />

      case CELL_TYPE_UNKNOWN:
        return <BlockImage alt="Unknown" src={`${IMAGE_BASE}/unknown.jpg`} />

      default:
        throw new Error(`Unknown cell type: ${type}`);
    }
  }
}


const InlineTable = styled.table`
  display: inline-table;
`;

const SquareTd = styled.td`
  height: 50px;
  width: 50px;
`;

export class OceanGrid extends React.PureComponent {
  onCellClicked(rowIdx, colIdx) {
    if (rowIdx < 0 || colIdx < 0) {
      // An indicator was clicked. Ignore it.
      return;
    }

    this.props.onCellClicked(rowIdx, colIdx);
  }

  render() {
    const { grid } = this.props;

    const headerColumns = [
      // First column is the corner, which does not need to say anything.
      <>&nbsp;</>,
    ];
    COL_INDICATORS.forEach(indicator => {
      headerColumns.push(<strong>{indicator}</strong>);
    });

    const rows = [headerColumns];
    ROW_INDICATORS.forEach(indicator => {
      const row = [<strong>{indicator}</strong>];
      // First row is the indicator row.
      const gridRowIndex = rows.length - 1;
      grid[gridRowIndex].forEach(gridCell => {
        row.push(<OceanCell type={gridCell} />);
      });
      rows.push(row);
    });

    return (
      <InlineTable cellSpacing="0" cellPadding="0">
        <tbody>
          {rows.map((row, rowIdx) => (
            <tr key={rowIdx}>
              {row.map((cell, colIdx) => (
                <SquareTd
                  key={colIdx}
                  align="center"
                  valign="center"
                  onClick={() => this.onCellClicked(rowIdx - 1, colIdx - 1)}
                >
                  {cell}
                </SquareTd>
              ))}
            </tr>
          ))}
        </tbody>
      </InlineTable>
    );
  }
}



const CenteredDiv = styled.div`
  text-align: center;
`;

const REVEALED_CELL_TYPES = [CELL_TYPE_OCEAN, CELL_TYPE_PLAYER_ONE, CELL_TYPE_PLAYER_TWO];
function randomRevealedCell() {
  return REVEALED_CELL_TYPES[Math.floor(Math.random() * REVEALED_CELL_TYPES.length)];
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
    return ROW_INDICATORS.map(() => COL_INDICATORS.map(() => CELL_TYPE_UNKNOWN));
  }

  async getOpponentGrid() {
    return ROW_INDICATORS.map(() => COL_INDICATORS.map(() => CELL_TYPE_UNKNOWN));
  }

  async componentDidMount() {
    const stateUpdate = {};
    stateUpdate.myGrid = await this.getMyGrid();
    stateUpdate.opponentGrid = await this.getOpponentGrid();
    this.setState(stateUpdate);
  }

  onMyCellClicked = (rowIdx, colIdx) => {
    const { myGrid } = this.state;
    if (myGrid[rowIdx][colIdx] !== CELL_TYPE_UNKNOWN) {
      // This cell is already revealed. Ignore this.
      return;
    }

    const newGridRows = [];
    myGrid.forEach((oldRow, oldRowIdx) => {
      const newGridRow = [];
      oldRow.forEach((oldCell, oldColIdx) => {
        if (rowIdx === oldRowIdx && colIdx === oldColIdx) {
          // This is the cell we are revealing.
          newGridRow.push(randomRevealedCell());
        } else {
          newGridRow.push(oldCell);
        }
      });
      newGridRows.push(newGridRow);
    });
    this.setState({
      myGrid: newGridRows,
    });
  };

  onOpponentCellClicked = (rowIdx, colIdx) => {
    const { opponentGrid } = this.state;
    if (opponentGrid[rowIdx][colIdx] !== CELL_TYPE_UNKNOWN) {
      // This cell is already revealed. Ignore this.
      return;
    }

    const newGridRows = [];
    opponentGrid.forEach((oldRow, oldRowIdx) => {
      const newGridRow = [];
      oldRow.forEach((oldCell, oldColIdx) => {
        if (rowIdx === oldRowIdx && colIdx === oldColIdx) {
          // This is the cell we are revealing.
          newGridRow.push(randomRevealedCell());
        } else {
          newGridRow.push(oldCell);
        }
      });
      newGridRows.push(newGridRow);
    });
    this.setState({
      opponentGrid: newGridRows,
    });
  };

  render() {
    const { myGrid, opponentGrid } = this.state;

    if (myGrid === null || opponentGrid === null) {
      return null;
    }

    return (
      <CenteredDiv>
        <img alt="ABACShip" src={`${IMAGE_BASE}/abacship.jpg`} />
        <CenteredDiv>
          <OceanGrid grid={myGrid} onCellClicked={this.onMyCellClicked} />
        </CenteredDiv>
        <CenteredDiv>
          <OceanGrid grid={opponentGrid} onCellClicked={this.onOpponentCellClicked} />
        </CenteredDiv>
      </CenteredDiv>
    );
  }
}
