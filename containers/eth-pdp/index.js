import http from 'http';
import express from 'express';
import logger from 'morgan';
import axios from 'axios';

// ETH Configs (main, kovan)
const ETH_CHAIN = 'main'; // TODO: make into an enum

const hostname = 'localhost';
const ethHostMain = 'https://api.ethplorer.io';
const ethHostKovan = 'https://kovan-api.ethplorer.io';
let ethHost = undefined;
const ethplorerApiKey = 'EK-ujRCx-M4SpUWd-Wm1wQ';

// App setup
const port = process.env.PORT || 8088;
const app = express() // setup express application
const server = http.createServer(app);

// Select appropraite eth network
if(ETH_CHAIN === 'kovan') {
  ethHost = ethHostKovan
}
else if(ETH_CHAIN === 'main') {
  ethHost = ethHostMain;
}

// Middleware
app.use(logger('dev')); // log requests to the console
app.use(express.json()); // Parse incoming requests data
app.use(express.urlencoded({ extended: true }));

// Endpoints
app.get('/confirmTransaction', async (req, res) => {
  const senderAddress = req.query.senderAddress.toLowerCase();
  const recipientAddress = req.query.recipientAddress.toLowerCase();
  const tier = req.query.tier;
  const value = req.query.value;

  try {
    const resp = await axios.get(`${ethHost}/getAddressTransactions/${senderAddress}`,
      {
        params: {
          apiKey: ethplorerApiKey
        }
      }
    );

    const transactionHistory = resp.data;

    const transaction = transactionHistory.find(transaction =>
      {
        return transaction.from === senderAddress && transaction.to === recipientAddress;
      }
    )

    if (!transaction) {
      throw new Error('Couldn\'t find transaction');
    }

    if(transaction.value < value) {
      throw new Error(`Transaction amount of ${transaction.value} eth is less than the required amount of ${value} eth`);
    }

    res.status(200).send();

  } catch (e) {
    console.error(e);
    res.status(500).send({
      Error: e.message
    });
  }
});

// Expose server
server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
