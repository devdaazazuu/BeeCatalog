import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, Send, Loader, AlertTriangle, CheckCircle } from 'lucide-react';
import api from '../services/api';

function Organizador() {
    const [csvFile, setCsvFile] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [feedbackMessage, setFeedbackMessage] = useState('');
    const [taskStatus, setTaskStatus] = useState('');
    const [generatedProducts, setGeneratedProducts] = useState([]);
    const [pollingIntervalId, setPollingIntervalId] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        return () => {
            if (pollingIntervalId) {
                clearInterval(pollingIntervalId);
            }
        };
    }, [pollingIntervalId]);

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file && file.type === 'text/csv') {
            setCsvFile(file);
            setFeedbackMessage(`Arquivo selecionado: ${file.name}`);
            setTaskStatus('');
            setGeneratedProducts([]);
        } else {
            setCsvFile(null);
            setFeedbackMessage('Por favor, selecione um arquivo .csv');
            setTaskStatus('error');
        }
    };

    const pollTaskStatus = (taskId) => {
        const intervalId = setInterval(async () => {
            try {
                const { data } = await api.get(`/task-status/${taskId}/`);
                if (data.status === 'SUCCESS') {
                    clearInterval(intervalId);
                    setPollingIntervalId(null);
                    setFeedbackMessage('Conteúdo gerado com sucesso!');
                    setTaskStatus('success');
                    setIsLoading(false);
                    setGeneratedProducts(data.result.products_data);
                } else if (data.status === 'FAILURE') {
                    clearInterval(intervalId);
                    setPollingIntervalId(null);
                    setIsLoading(false);
                    setFeedbackMessage('Ocorreu um erro ao gerar o conteúdo.');
                    setTaskStatus('error');
                } else if (data.status === 'PROGRESS') {
                    const meta = data.result;
                    if (meta && meta.step) {
                        setFeedbackMessage(`${meta.step}: Processando produto ${meta.current} de ${meta.total}...`);
                    }
                }
            } catch (error) {
                clearInterval(intervalId);
                setPollingIntervalId(null);
                setIsLoading(false);
                setFeedbackMessage('Erro ao consultar o estado da tarefa.');
                setTaskStatus('error');
            }
        }, 3000);
        setPollingIntervalId(intervalId);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!csvFile) {
            setFeedbackMessage('Nenhum arquivo CSV selecionado.');
            setTaskStatus('error');
            return;
        }
        setIsLoading(true);
        setFeedbackMessage('Enviando arquivo para processamento...');
        setTaskStatus('loading');
        setGeneratedProducts([]);

        const formData = new FormData();
        formData.append('product_info_csv', csvFile);

        try {
            const response = await api.post('/organizador-ia/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            const { task_id } = response.data;
            setFeedbackMessage('Processamento iniciado! Aguardando o resultado...');
            pollTaskStatus(task_id);
        } catch (error) {
            setIsLoading(false);
            setFeedbackMessage('Erro ao enviar o arquivo.');
            setTaskStatus('error');
            console.error("Erro no envio do CSV:", error);
        }
    };

    const handleSendToListingPage = () => {
        navigate('/listagem', { state: { products: generatedProducts } });
    };

    const getStatusIcon = () => {
        switch (taskStatus) {
            case 'loading':
                return <Loader className="animate-spin text-yellow-400" />;
            case 'success':
                return <CheckCircle className="text-green-400" />;
            case 'error':
                return <AlertTriangle className="text-red-400" />;
            default:
                return <FileText className="text-gray-500" />;
        }
    };

    return (
        <div>
            <h1 className="text-3xl font-bold uppercase text-yellow-400 mb-2">Organizador de Conteúdo</h1>
            <p className="text-gray-400 mb-6">Envie um arquivo CSV com as informações básicas dos seus produtos e a IA irá gerar o título, descrição, bullet points e palavras-chave para o seu listing da Amazon.</p>

            <div className="p-6 bg-gray-800/50 rounded-lg border border-yellow-500/20">
                <form onSubmit={handleSubmit}>
                    <div className="bg-black/20 p-6 rounded-lg flex flex-col items-center justify-center border-2 border-dashed border-gray-600 hover:border-yellow-500 transition-colors">
                        <UploadCloud className="w-12 h-12 text-gray-500 mb-4" />
                        <label htmlFor="csv_upload" className="relative cursor-pointer bg-yellow-500/20 text-yellow-300 hover:bg-yellow-500/30 font-semibold rounded-md px-4 py-2 text-sm transition-colors">
                            <span>{csvFile ? 'Trocar Arquivo' : 'Selecionar Arquivo CSV'}</span>
                            <input id="csv_upload" name="csv_upload" type="file" className="sr-only" accept=".csv" onChange={handleFileChange} />
                        </label>
                        <p className="text-xs text-gray-500 mt-2">Apenas arquivos .csv são permitidos.</p>
                    </div>

                    {feedbackMessage && (
                        <div className="mt-4 p-4 bg-gray-700/50 rounded-lg flex items-center gap-4">
                            <div className="flex-shrink-0">{getStatusIcon()}</div>
                            <p className="text-gray-300 text-sm">{feedbackMessage}</p>
                        </div>
                    )}

                    <div className="mt-6 text-right">
                        <button type="submit" className="px-6 py-2 font-bold text-black bg-yellow-400 rounded-lg hover:bg-yellow-500 disabled:bg-gray-600 disabled:cursor-not-allowed" disabled={!csvFile || isLoading}>
                            {isLoading ? 'Processando...' : 'Gerar Conteúdo com IA'}
                        </button>
                    </div>
                </form>
            </div>

            {generatedProducts.length > 0 && (
                <div className="mt-8 p-6 bg-gray-800/50 rounded-lg border border-green-500/30">
                    <h2 className="text-2xl font-bold text-green-400 mb-4">Conteúdo Gerado</h2>
                    <p className="text-gray-400 mb-4">
                        A IA gerou o conteúdo para <span className="font-bold text-white">{generatedProducts.length}</span> produto(s). Você pode agora enviar estes dados para a página de "Criar Listing" para validar, editar e gerar a planilha final.
                    </p>
                    <div className="text-right mt-6">
                        <button onClick={handleSendToListingPage} className="flex items-center justify-center gap-2 ml-auto px-6 py-3 text-lg font-bold text-black bg-green-400 rounded-lg hover:bg-green-500">
                            <Send size={20} />
                            <span>Enviar para Criar Listing</span>
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Organizador;
