<template>
  <div class="book-container">

    <!-- Header & Search -->
    <div class="book-header">

      <div>
        <h2 class="book-title">
          📚 Book List
        </h2>

        <!-- Custom Utility Function Call (Greeting) -->
        <p class="greeting">
          {{ userGreeting }}
        </p>
      </div>

      <div class="book-actions">

        <!-- Search Box -->
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search book..."
          class="search-input"
        />

        <!-- Refresh Button -->
        <button
          @click="fetchBooks"
          class="refresh-button"
        >
          🔄 Refresh
        </button>

      </div>

    </div>


    <!-- Loading Text -->
    <p v-if="loading">
      Loading books from Frappe...
    </p>


    <!-- Empty State -->
    <p v-else-if="filteredBooks.length === 0">
      No books found!
    </p>


    <!-- Book List -->
    <ul v-else class="book-list">

      <li
        v-for="book in filteredBooks"
        :key="book.name"
        class="book-item"
      >

        <b>
          {{ book.book_name }}
        </b>

        - ₹{{ book.price || 0 }}

        (Stock: {{ book.available_qty || 0 }})

        <br />

        <!-- Custom Utility Function Call -->
        <span class="stock-value">
          Total Stock Value:
          ₹{{ calculateTotal(
            book.price || 0,
            book.available_qty || 0
          ) }}
        </span>

      </li>

    </ul>

  </div>
</template>


<script setup>

import { ref, computed, onMounted } from 'vue';

// Custom JS Utility Functions
import { greetUser, calculateTotal } from './book_utils.js';


// 1. Storage Variables

const books = ref([]);

const loading = ref(true);

const searchQuery = ref('');

const userGreeting = ref('');


// 2. Fetch Data from Database

const fetchBooks = async () => {

  loading.value = true;

  const response = await frappe.call({

    method: 'frappe.client.get_list',

    args: {

      doctype: 'Book',

      fields: [
        'name',
        'book_name',
        'price',
        'available_qty'
      ]

    }

  });

  books.value = response.message || [];

  loading.value = false;

};


// 3. Search Filter

const filteredBooks = computed(() => {

  if (!searchQuery.value) {
    return books.value;
  }

  const query = searchQuery.value.toLowerCase();

  return books.value.filter(book =>
    book.book_name &&
    book.book_name.toLowerCase().includes(query)
  );

});


// 4. Page load execution

onMounted(() => {

  userGreeting.value = greetUser("Pradeep");

  fetchBooks();

});

</script>


<style>

/* ============================= */
/* Desktop / Default Layout      */
/* ============================= */

.book-container {
  padding: 20px;
  font-family: sans-serif;
}


/* Header */

.book-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}


/* Title */

.book-title {
  margin: 0;
}


/* Greeting */

.greeting {
  margin: 4px 0 0 0;
  color: #4f46e5;
  font-weight: bold;
  font-size: 14px;
}


/* Search + Refresh */

.book-actions {
  display: flex;
  gap: 10px;
}


/* Search */

.search-input {
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 6px;
}


/* Refresh */

.refresh-button {
  padding: 8px 15px;
  border: none;
  background: #4f46e5;
  color: white;
  border-radius: 6px;
  cursor: pointer;
}


/* Book List */

.book-list {
  padding-left: 20px;
}


/* Book Item */

.book-item {
  margin-bottom: 12px;
}


/* Total Stock Value */

.stock-value {
  color: #10b981;
  font-size: 13px;
}


/* ============================= */
/* Mobile Responsive Design      */
/* ============================= */

@media (max-width: 600px) {

  /* Header becomes vertical */

  .book-header {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }


  /* Search and Refresh become vertical */

  .book-actions {
    flex-direction: column;
    gap: 10px;
  }


  /* Full width on mobile */

  .search-input,
  .refresh-button {
    width: 100%;
    box-sizing: border-box;
  }


  /* Bigger touch area */

  .refresh-button {
    min-height: 44px;
  }

}

</style>