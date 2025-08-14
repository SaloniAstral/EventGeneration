// MongoDB Initialization Script
// Sets up the financial data database and collections

// Switch to the stockdata database
db = db.getSiblingDB('stockdata');

// Create collections with validation
db.createCollection('stock_data', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["symbol", "date", "close_price"],
      properties: {
        symbol: {
          bsonType: "string",
          description: "Stock symbol - required"
        },
        date: {
          bsonType: "string",
          description: "Trading date - required"
        },
        close_price: {
          bsonType: "number",
          description: "Closing price - required"
        },
        open_price: {
          bsonType: "number"
        },
        high_price: {
          bsonType: "number"
        },
        low_price: {
          bsonType: "number"
        },
        volume: {
          bsonType: "number"
        }
      }
    }
  }
});

db.createCollection('company_info', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["symbol", "name"],
      properties: {
        symbol: {
          bsonType: "string",
          description: "Stock symbol - required"
        },
        name: {
          bsonType: "string",
          description: "Company name - required"
        },
        sector: {
          bsonType: "string"
        },
        industry: {
          bsonType: "string"
        },
        description: {
          bsonType: "string"
        }
      }
    }
  }
});

db.createCollection('stock_ticks', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["symbol", "timestamp", "price"],
      properties: {
        symbol: {
          bsonType: "string",
          description: "Stock symbol - required"
        },
        timestamp: {
          bsonType: "string",
          description: "Tick timestamp - required"
        },
        price: {
          bsonType: "number",
          description: "Current price - required"
        },
        price_change: {
          bsonType: "number"
        },
        volume: {
          bsonType: "number"
        },
        stream_type: {
          bsonType: "string"
        }
      }
    }
  }
});

db.createCollection('events', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["event_type", "event_source", "timestamp"],
      properties: {
        event_type: {
          bsonType: "string",
          description: "Event type - required"
        },
        event_source: {
          bsonType: "string",
          description: "Event source - required"
        },
        timestamp: {
          bsonType: "string",
          description: "Event timestamp - required"
        },
        event_id: {
          bsonType: "string"
        },
        metadata: {
          bsonType: "object"
        }
      }
    }
  }
});

db.createCollection('fetch_operations', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["symbol", "status", "timestamp"],
      properties: {
        symbol: {
          bsonType: "string",
          description: "Stock symbol - required"
        },
        status: {
          bsonType: "string",
          description: "Operation status - required"
        },
        timestamp: {
          bsonType: "string",
          description: "Operation timestamp - required"
        },
        records_fetched: {
          bsonType: "number"
        },
        error_message: {
          bsonType: "string"
        }
      }
    }
  }
});

// Create indexes for better performance
db.stock_data.createIndex({ "symbol": 1, "date": -1 });
db.stock_data.createIndex({ "symbol": 1 });
db.stock_data.createIndex({ "date": -1 });

db.company_info.createIndex({ "symbol": 1 }, { unique: true });
db.company_info.createIndex({ "sector": 1 });

db.stock_ticks.createIndex({ "symbol": 1, "timestamp": -1 });
db.stock_ticks.createIndex({ "timestamp": -1 });
db.stock_ticks.createIndex({ "stream_type": 1 });

db.events.createIndex({ "event_type": 1, "timestamp": -1 });
db.events.createIndex({ "event_source": 1, "timestamp": -1 });
db.events.createIndex({ "timestamp": -1 });

db.fetch_operations.createIndex({ "symbol": 1, "timestamp": -1 });
db.fetch_operations.createIndex({ "status": 1, "timestamp": -1 });

// Insert sample data for testing
db.stock_data.insertMany([
  {
    symbol: "AAPL",
    date: "2024-01-15",
    open_price: 150.00,
    high_price: 152.50,
    low_price: 149.75,
    close_price: 151.25,
    volume: 50000000
  },
  {
    symbol: "GOOGL",
    date: "2024-01-15",
    open_price: 2800.00,
    high_price: 2825.00,
    low_price: 2795.00,
    close_price: 2810.50,
    volume: 25000000
  }
]);

db.company_info.insertMany([
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    sector: "Technology",
    industry: "Consumer Electronics",
    description: "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide."
  },
  {
    symbol: "GOOGL",
    name: "Alphabet Inc.",
    sector: "Technology",
    industry: "Internet Content & Information",
    description: "Alphabet Inc. provides online advertising services in the United States, Europe, the Middle East, Africa, the Asia-Pacific, Canada, and Latin America."
  }
]);

print("✅ MongoDB initialization completed successfully!");
print("📊 Created collections: stock_data, company_info, stock_ticks, events, fetch_operations");
print("📈 Created indexes for optimal performance");
print("🧪 Inserted sample data for testing"); 