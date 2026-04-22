import React, { useState, useEffect } from 'react';

// Define the structure for our Book object
interface Book {
    id?: string;
    title: string;
    author: string;
    genre: string;
    summary: string;
    publication_date?: string;
    publisher?: string;
    edition?: string;
    search_times?: number;
}

const AdminPanel: React.FC = () => {
    // 1. State for the list of books and the form
    const [books, setBooks] = useState<Book[]>([]);
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState<Book>({
        title: '',
        author: '',
        genre: '',
        summary: '',
        publication_date: '2024-01-01', // Default date to match ES mapping
        publisher: '',
        edition: '1'
    });

    // 2. Fetch current inventory from Elasticsearch
    const fetchInventory = async () => {
        try {
            const response = await fetch('http://127.0.0.1:5000/elasticsearch/popular?order=desc');
            const result = await response.json();
            if (Array.isArray(result.data)) {
                setBooks(result.data);
            }
        } catch (error) {
            console.error("Error fetching inventory:", error);
        }
    };

    useEffect(() => {
        fetchInventory();
    }, []);

    // 3. Handle Form Submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            // Backend expects an array of books, so we wrap formData in []
            const response = await fetch('http://127.0.0.1:5000/elasticsearch/insert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify([formData]),
            });

            const result = await response.json();

            if (response.ok) {
                alert("Book added successfully to Elasticsearch!");
                // Reset form
                setFormData({
                    title: '', author: '', genre: '', summary: '',
                    publication_date: '2024-01-01', publisher: '', edition: '1'
                });
                fetchInventory(); // Refresh the table
            } else {
                alert("Error: " + result.message);
            }
        } catch (error) {
            alert("Connection failed. Is the Flask server running?");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: '40px', backgroundColor: '#1a202c', minHeight: '100 screen', color: 'white' }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '20px' }}>
                Campus Library Resource (Admin)
            </h1>

            {/* --- ADD NEW BOOK SECTION --- */}
            <div style={{ backgroundColor: '#2d3748', padding: '24px', borderRadius: '8px', marginBottom: '40px' }}>
                <h2 style={{ fontSize: '1.25rem', marginBottom: '16px' }}>Add New Inventory</h2>
                <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <input 
                        type="text" placeholder="Book Title" required
                        value={formData.title}
                        onChange={(e) => setFormData({...formData, title: e.target.value})}
                        style={{ padding: '8px', borderRadius: '4px', backgroundColor: '#4a5568', color: 'white', border: 'none' }}
                    />
                    <input 
                        type="text" placeholder="Author" required
                        value={formData.author}
                        onChange={(e) => setFormData({...formData, author: e.target.value})}
                        style={{ padding: '8px', borderRadius: '4px', backgroundColor: '#4a5568', color: 'white', border: 'none' }}
                    />
                    <input 
                        type="text" placeholder="Genre" required
                        value={formData.genre}
                        onChange={(e) => setFormData({...formData, genre: e.target.value})}
                        style={{ padding: '8px', borderRadius: '4px', backgroundColor: '#4a5568', color: 'white', border: 'none' }}
                    />
                    <input 
                        type="date" placeholder="Pub Date (yyyy-mm-dd)"
                        value={formData.publication_date}
                        onChange={(e) => setFormData({...formData, publication_date: e.target.value})}
                        style={{ padding: '8px', borderRadius: '4px', backgroundColor: '#4a5568', color: 'white', border: 'none' }}
                    />
                    <textarea 
                        placeholder="Book Summary (Required for Semantic Search)" required
                        value={formData.summary}
                        onChange={(e) => setFormData({...formData, summary: e.target.value})}
                        style={{ gridColumn: 'span 2', padding: '8px', borderRadius: '4px', backgroundColor: '#4a5568', color: 'white', border: 'none', minHeight: '80px' }}
                    />
                    <button 
                        type="submit" 
                        disabled={loading}
                        style={{ gridColumn: 'span 2', padding: '12px', backgroundColor: '#4299e1', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', border: 'none' }}
                    >
                        {loading ? 'Processing...' : 'Add to Inventory'}
                    </button>
                </form>
            </div>

            {/* --- INVENTORY LIST SECTION --- */}
            <div style={{ backgroundColor: '#2d3748', padding: '24px', borderRadius: '8px' }}>
                <h2 style={{ fontSize: '1.25rem', marginBottom: '16px' }}>Current Inventory (Top Search Times)</h2>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid #4a5568', textAlign: 'left' }}>
                            <th style={{ padding: '12px' }}>Title</th>
                            <th style={{ padding: '12px' }}>Author</th>
                            <th style={{ padding: '12px' }}>Genre</th>
                            <th style={{ padding: '12px' }}>popularity</th>
                        </tr>
                    </thead>
                    <tbody>
                        {books.length > 0 && typeof books !== 'string' ? books.map((book) => (
                            <tr key={book.id} style={{ borderBottom: '1px solid #4a5568' }}>
                                <td style={{ padding: '12px' }}>{book.title}</td>
                                <td style={{ padding: '12px' }}>{book.author}</td>
                                <td style={{ padding: '12px' }}>{book.genre}</td>
                                <td style={{ padding: '12px' }}>{book.search_times} views</td>
                            </tr>
                        )) : (
                            <tr><td colSpan={4} style={{ padding: '20px', textAlign: 'center' }}>No books found.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AdminPanel;
