import React, { useState, useEffect } from 'react';
import api from '../services/api';

function ExtrairImagens() {
    const [link, setLink] = useState('');
    const [images, setImages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [feedbackMessage, setFeedbackMessage] = useState('');
    const [pollingIntervalId, setPollingIntervalId] = useState(null);

    useEffect(() => {
        return () => {
            if (pollingIntervalId) {
                clearInterval(pollingIntervalId);
            }
        };
    }, [pollingIntervalId]);

    const pollTaskStatus = (taskId) => {
        const intervalId = setInterval(async () => {
            try {
                const { data } = await api.get(`/task-status/${taskId}/`);

                if (data.status === 'SUCCESS') {
                    clearInterval(intervalId);
                    setPollingIntervalId(null);
                    setImages(data.result.image_urls || []);
                    setFeedbackMessage('Imagens extraídas com sucesso!');
                    setIsLoading(false);
                } else if (data.status === 'FAILURE') {
                    clearInterval(intervalId);
                    setPollingIntervalId(null);
                    const errorMessage = data.result?.exc_message || 'Ocorreu um erro desconhecido.';
                    setFeedbackMessage(`Erro: ${errorMessage}`);
                    setIsLoading(false);
                } else if (data.status === 'PROGRESS') {
                    setFeedbackMessage(data.result?.step || 'Extraindo imagens...');
                }

            } catch (error) {
                clearInterval(intervalId);
                setPollingIntervalId(null);
                setIsLoading(false);
                setFeedbackMessage('Erro ao consultar o estado da tarefa.');
                console.error("Erro de polling:", error);
            }
        }, 2000);
        setPollingIntervalId(intervalId);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!link) return;

        setIsLoading(true);
        setImages([]);
        setFeedbackMessage('Enviando solicitação...');

        try {
            const response = await api.post('/scrape-images/', { link });
            const { task_id } = response.data;
            setFeedbackMessage('Processamento iniciado! Aguardando resultado...');
            pollTaskStatus(task_id);
        } catch (error) {
            setIsLoading(false);
            const errorMsg = error.response?.data?.error || 'Não foi possível iniciar a extração.';
            setFeedbackMessage(`Erro: ${errorMsg}`);
            console.error("Erro ao iniciar a extração:", error);
        }
    };

    return (
        <div>
            <h1 className="text-3xl font-bold uppercase text-yellow-400 mb-6">Extrair Imagens Mercado Livre</h1>
            <div className="p-6 bg-gray-800/50 rounded-lg border border-yellow-500/20">
                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label htmlFor="link" className="block mb-2 text-sm font-medium text-gray-300">Link do Anúncio:</label>
                        <input 
                            type="url" 
                            name="link" 
                            id="link"
                            value={link}
                            onChange={(e) => setLink(e.target.value)}
                            placeholder="https://produto.mercadolivre.com.br/..."
                            className="w-full px-3 py-2 text-white bg-gray-700 border border-gray-600 rounded-lg focus:ring-yellow-500 focus:border-yellow-500"
                            required
                        />
                    </div>
                    <button type="submit" className="px-6 py-2 font-bold text-black bg-yellow-400 rounded-lg hover:bg-yellow-500 disabled:bg-gray-600" disabled={isLoading}>
                        {isLoading ? 'Extraindo...' : 'Extrair'}
                    </button>
                </form>
            </div>

            {isLoading && (
                 <div className="mt-8 text-center">
                    <p className="text-yellow-400">{feedbackMessage}</p>
                    <div className="w-8 h-8 border-2 border-dashed rounded-full animate-spin border-yellow-400 mx-auto mt-4"></div>
                </div>
            )}

            {!isLoading && feedbackMessage && images.length === 0 && (
                 <div className="mt-8 text-center p-4 bg-red-900/50 rounded-lg">
                    <p className="text-red-300">{feedbackMessage}</p>
                </div>
            )}

            {images.length > 0 && !isLoading && (
                <div className="mt-12">
                    <h2 className="text-2xl font-bold text-yellow-400 mb-6">Imagens Extraídas ({images.length})</h2>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                        {images.map((imgUrl, index) => (
                        <div key={index} className="overflow-hidden rounded-lg shadow-lg bg-gray-800 border border-gray-700">
                            <img src={imgUrl} alt={`Imagem do produto ${index + 1}`} className="object-cover w-full h-48" />
                        </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default ExtrairImagens;
