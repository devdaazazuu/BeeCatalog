import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, useOutletContext } from 'react-router-dom';
import { Plus, Trash2, ChevronDown, Image as ImageIcon, UploadCloud, FileText, Package } from 'lucide-react';
import api from '../services/api';
import LoadingScreen from '../components/LoadingScreen';
import useNotification from '../hooks/useNotification';

// Utility functions
const createNewVariation = () => ({ id: Date.now(), sku: '', tipo: '', cor: '', cla: '', peso: '', imagem: '' });
const createNewExtraImage = () => ({ id: Date.now(), file: null });
const createNewProduct = (initialData = {}, index = 0) => ({
    id: initialData.id || Date.now() + index,
    titulo: initialData.titulo || '', sku: initialData.sku || '', tipo_marca: initialData.tipo_marca || '', nome_marca: initialData.nome_marca || '', preco: initialData.preco || '', fba_dba: initialData.fba_dba || '',
    id_produto: initialData.id_produto || '', tipo_id_produto: initialData.tipo_id_produto || '', ncm: initialData.ncm || '', quantidade: initialData.quantidade || '', peso_pacote: initialData.peso_pacote || '',
    c_l_a_pacote: initialData.c_l_a_pacote || '', peso_produto: initialData.peso_produto || '', c_l_a_produto: initialData.c_l_a_produto || '', ajuste: initialData.ajuste || '',
    variacoes: (initialData.variacoes || []).map(v => ({...v, id: v.id || Date.now()})),
    imagens: initialData.imagens || { principal: null, amostra: null, extra: [] }
});

const downloadBase64File = (base64Data, fileName) => {
    try {
        // Verifica se base64Data é válido
        if (!base64Data || typeof base64Data !== 'string') {
            throw new Error('Dados base64 inválidos ou não fornecidos');
        }
        
        // Remove prefixo data:... se existir
        let cleanBase64 = base64Data;
        if (base64Data.includes(',')) {
            cleanBase64 = base64Data.split(',')[1];
        }
        
        // Remove caracteres inválidos e espaços em branco
        cleanBase64 = cleanBase64.replace(/[^A-Za-z0-9+/=]/g, '');
        
        // Adiciona padding se necessário
        while (cleanBase64.length % 4) {
            cleanBase64 += '=';
        }
        
        const byteCharacters = atob(cleanBase64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/vnd.ms-excel.sheet.macroEnabled.12' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);
    } catch (error) {
        console.error("Erro ao tentar fazer o download do arquivo:", error);
        alert('Erro ao fazer download do arquivo. Verifique se o arquivo está correto.');
    }
};

const InputField = ({ label, name, id, value, onChange, type = 'text', placeholder = '', required = false, span = 'col-span-1' }) => (
    <div className={span}>
        <label htmlFor={id} className="block mb-3 text-sm font-medium text-gray-300">{label}</label>
        <input id={id} name={name} type={type} value={value} onChange={onChange} placeholder={placeholder} className="w-full px-4 py-3 text-white bg-black/30 backdrop-blur-sm border border-gray-600/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/50 transition-all duration-300 hover:border-gray-500/50" />
    </div>
);

const SelectField = ({ label, name, id, value, onChange, children, span = 'col-span-1' }) => (
    <div className={span}>
        <label htmlFor={id} className="block mb-3 text-sm font-medium text-gray-300">{label}</label>
        <select id={id} name={name} value={value} onChange={onChange} className="w-full px-4 py-3 text-white bg-black/30 backdrop-blur-sm border border-gray-600/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/50 transition-all duration-300 hover:border-gray-500/50">{children}</select>
    </div>
);

const ImageUploadField = ({ label, id, required, onImageChange }) => {
    const [preview, setPreview] = useState(null);
    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            const previewUrl = URL.createObjectURL(file);
            setPreview(previewUrl);
            onImageChange(file);
        } else {
            setPreview(null);
            onImageChange(null);
        }
    };
    useEffect(() => { return () => { if (preview) URL.revokeObjectURL(preview); }; }, [preview]);
    return (
        <div className="w-full">
            <label htmlFor={id} className="block mb-3 text-sm font-medium text-gray-300">{label}{required && <span className="text-red-500">*</span>}</label>
            <div className="flex items-center gap-4 p-6 bg-black/30 backdrop-blur-sm border border-gray-600/50 rounded-xl hover:border-gray-500/50 transition-all duration-300">
                <input id={id} type="file" accept="image/*" onChange={handleFileChange} className="block w-full text-sm text-gray-400 file:mr-4 file:py-3 file:px-6 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-gradient-to-r file:from-amber-500/20 file:to-amber-400/20 file:text-amber-300 hover:file:from-amber-500/30 hover:file:to-amber-400/30 file:transition-all file:duration-300" />
                {preview ? <img src={preview} alt="Preview" className="h-20 w-20 object-cover rounded-xl border border-gray-600/50 shadow-lg" /> : <div className="h-20 w-20 flex-shrink-0 flex items-center justify-center bg-gray-700/50 rounded-xl border border-gray-600/50"><ImageIcon className="text-gray-500" /></div>}
            </div>
        </div>
    );
};

const VariationForm = ({ variacao, productSku, index, handleVariationChange, removeVariation }) => {
    const generateSku = () => {
        const parentSku = productSku || "PRODUTO";
        const newSku = `${parentSku}-VAR${index + 1}-${Date.now().toString().slice(-4)}`;
        const fakeEvent = { target: { name: 'sku', value: newSku } };
        handleVariationChange(variacao.id, fakeEvent);
    };
    return (
        <div className="bg-gray-700/30 backdrop-blur-sm rounded-xl border border-gray-600/50 hover:border-gray-500/50 transition-all duration-300">
            <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                    <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                            {index + 1}
                        </div>
                        <h4 className="text-md font-semibold text-white">Variação {index + 1}</h4>
                    </div>
                    <button 
                        type="button" 
                        onClick={() => removeVariation(variacao.id)} 
                        className="px-3 py-1.5 text-red-400 hover:text-white bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 hover:border-red-500/50 rounded-lg transition-all duration-300 text-sm font-medium"
                    >
                        <Trash2 size={16} className="inline mr-2" />Remover
                    </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="md:col-span-2"><InputField label={`SKU da Variação ${index + 1}`} name="sku" id={`var-sku-${variacao.id}`} value={variacao.sku} onChange={(e) => handleVariationChange(variacao.id, e)} /></div>
                    <div className="flex items-end"><button type="button" onClick={generateSku} className="w-full h-10 px-4 text-sm font-bold text-black bg-gradient-to-r from-amber-400 to-amber-500 rounded-xl hover:from-amber-500 hover:to-amber-600 transition-all duration-300">Gerar SKU</button></div>
                </div>
                <SelectField label="Tipo de Variação" name="tipo" id={`var-tipo-${variacao.id}`} value={variacao.tipo} onChange={(e) => handleVariationChange(variacao.id, e)}><option value="">Selecione o tipo...</option><option value="cor">Cor</option><option value="c_l_a_p">Tamanho e Peso</option></SelectField>
                {variacao.tipo === 'cor' && (<InputField label="Nome da Cor" name="cor" id={`var-cor-${variacao.id}`} value={variacao.cor} onChange={(e) => handleVariationChange(variacao.id, e)} />)}
                {variacao.tipo === 'c_l_a_p' && (<div className="grid grid-cols-1 md:grid-cols-2 gap-4"><InputField label="Dimensões (C x L x A)" name="cla" id={`var-cla-${variacao.id}`} value={variacao.cla} onChange={(e) => handleVariationChange(variacao.id, e)} placeholder="ex: 18x13x8" /><InputField label="Peso do Produto (g)" name="peso" id={`var-peso-${variacao.id}`} value={variacao.peso} onChange={(e) => handleVariationChange(variacao.id, e)} type="number" /></div>)}
                <InputField label="URL Imagem Principal da Variação" name="imagem" id={`var-img-${variacao.id}`} value={variacao.imagem} onChange={(e) => handleVariationChange(variacao.id, e)} />
            </div>
        </div>
    );
};

const ProductForm = ({ product, index, removeProduct, handleProductChange, handleVariationChange, addVariation, removeVariation, handleImageChange, addExtraImage, removeExtraImage, handleExtraImageChange }) => {
    const [isExpanded, setIsExpanded] = useState(true);
    const toggleExpansion = () => setIsExpanded(!isExpanded);
    const handleRemoveClick = (e) => { e.stopPropagation(); removeProduct(product.id); };
    const showNomeMarca = product.tipo_marca === 'Marca';
    const showNcm = product.fba_dba === 'FBA';
    const showQuantidade = product.fba_dba === 'FBA';
    const showTipoId = product.id_produto !== '';
    return (
        <div className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 backdrop-blur-sm rounded-2xl border border-amber-500/20 hover:border-amber-500/30 transition-all duration-300 shadow-xl">
            <div className="p-8">
                <div className="flex justify-between items-center mb-6">
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl flex items-center justify-center text-white font-bold">
                            {index + 1}
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">Listagem - {product.titulo || `Produto ${index + 1}`}</h2>
                            <p className="text-sm text-gray-400">Configure os detalhes do produto</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button onClick={toggleExpansion} className="p-2 text-gray-400 hover:text-white transition-colors" aria-label="Expandir/Recolher">
                            <ChevronDown size={24} className={`transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} />
                        </button>
                        <button 
                            onClick={handleRemoveClick} 
                            className="px-4 py-2 text-red-400 hover:text-white bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 hover:border-red-500/50 rounded-xl transition-all duration-300 font-medium" 
                            aria-label="Remover Produto"
                        >
                            <Trash2 size={16} className="inline mr-2" />Remover
                        </button>
                    </div>
                </div>
                <div className={`transition-all duration-500 ease-in-out overflow-hidden ${isExpanded ? 'max-h-[5000px]' : 'max-h-0'}`}>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <InputField label="Título do Produto" name="titulo" id={`titulo-${product.id}`} value={product.titulo} onChange={(e) => handleProductChange(product.id, e)} required span="md:col-span-3" />
                    <InputField label="SKU" name="sku" id={`sku-${product.id}`} value={product.sku} onChange={(e) => handleProductChange(product.id, e)} />
                    <SelectField label="Tipo de Marca" name="tipo_marca" id={`tipo_marca-${product.id}`} value={product.tipo_marca} onChange={(e) => handleProductChange(product.id, e)}><option value="">Selecione...</option><option value="Genérico">Genérico</option><option value="Marca">Marca</option></SelectField>
                    {showNomeMarca && <InputField label="Nome da Marca" name="nome_marca" id={`nome_marca-${product.id}`} value={product.nome_marca} onChange={(e) => handleProductChange(product.id, e)} />}
                    <InputField label="Preço" name="preco" id={`preco-${product.id}`} value={product.preco} onChange={(e) => handleProductChange(product.id, e)} type="number" />
                    <SelectField label="FBA ou DBA" name="fba_dba" id={`fba_dba-${product.id}`} value={product.fba_dba} onChange={(e) => handleProductChange(product.id, e)}><option value="">Selecione...</option><option value="FBA">FBA</option><option value="DBA">DBA</option></SelectField>
                    <InputField label="ID do produto" name="id_produto" id={`id_produto-${product.id}`} value={product.id_produto} onChange={(e) => handleProductChange(product.id, e)} />
                    {showTipoId && (<SelectField label="Tipo de ID do Produto" name="tipo_id_produto" id={`tipo_id_produto-${product.id}`} value={product.tipo_id_produto} onChange={(e) => handleProductChange(product.id, e)}><option value="">Selecione...</option><option value="EAN">EAN</option><option value="GTIN">GTIN</option><option value="UPC">UPC</option></SelectField>)}
                    {showNcm && <InputField label="NCM" name="ncm" id={`ncm-${product.id}`} value={product.ncm} onChange={(e) => handleProductChange(product.id, e)} />}
                    {showQuantidade && <InputField label="Quantidade de Estoque" name="quantidade" id={`quantidade-${product.id}`} value={product.quantidade} onChange={(e) => handleProductChange(product.id, e)} type="number" />}
                    <InputField label="Peso do Pacote (g)" name="peso_pacote" id={`peso_pacote-${product.id}`} value={product.peso_pacote} onChange={(e) => handleProductChange(product.id, e)} type="number" span="md:col-span-2" />
                    <InputField label="Dimensões (pacote) C x L x A" name="c_l_a_pacote" id={`c_l_a_pacote-${product.id}`} value={product.c_l_a_pacote} onChange={(e) => handleProductChange(product.id, e)} placeholder="ex: 20x15x10" span="md:col-span-2" />
                    <InputField label="Peso do Produto (g)" name="peso_produto" id={`peso_produto-${product.id}`} value={product.peso_produto} onChange={(e) => handleProductChange(product.id, e)} type="number" span="md:col-span-2" />
                    <InputField label="Dimensões (produto) C x L x A" name="c_l_a_produto" id={`c_l_a_produto-${product.id}`} value={product.c_l_a_produto} onChange={(e) => handleProductChange(product.id, e)} placeholder="ex: 18x13x8" span="md:col-span-2" />
                    <SelectField label="O Produto é Ajustável?" name="ajuste" id={`ajuste-${product.id}`} value={product.ajuste} onChange={(e) => handleProductChange(product.id, e)} span="md:col-span-2"><option value="">Selecione...</option><option value="NÃO">Não</option><option value="SIM">Sim</option></SelectField>
                    <div className="md:col-span-4 mt-8">
                        <div className="bg-black/20 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
                            <div className="flex justify-between items-center mb-6">
                                <div className="flex items-center space-x-3">
                                    <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-green-600 rounded-lg flex items-center justify-center">
                                        <span className="text-white text-sm font-bold">V</span>
                                    </div>
                                    <h3 className="text-lg font-semibold text-white">Variações do Produto</h3>
                                </div>
                                <button 
                                    type="button" 
                                    onClick={() => addVariation(product.id)} 
                                    className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-black bg-gradient-to-r from-green-400 to-green-500 rounded-xl hover:from-green-500 hover:to-green-600 transition-all duration-300 transform hover:scale-[1.02] shadow-lg"
                                >
                                    <Plus size={16} />Adicionar Variação
                                </button>
                            </div>
                            <div className="space-y-4">{product.variacoes.map((variacao, varIndex) => (<VariationForm key={variacao.id} variacao={variacao} productSku={product.sku} index={varIndex} handleVariationChange={(variationId, e) => handleVariationChange(product.id, variationId, e)} removeVariation={() => removeVariation(product.id, variacao.id)} />))}</div>
                        </div>
                    </div>
                    <div className="md:col-span-4 mt-4 border-t border-amber-500/20 pt-4 space-y-4">
                        <h3 className="text-lg font-semibold text-amber-400">Imagens do Produto</h3>
                        <ImageUploadField label="Imagem Principal" id={`img-principal-${product.id}`} required onImageChange={(file) => handleImageChange(product.id, 'principal', file)} />
                        <ImageUploadField label="Imagem de Amostra" id={`img-amostra-${product.id}`} required onImageChange={(file) => handleImageChange(product.id, 'amostra', file)} />
                        <div className="bg-black/20 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 mt-6">
                            <div className="flex justify-between items-center mb-6">
                                <div className="flex items-center space-x-3">
                                    <div className="w-8 h-8 bg-gradient-to-r from-pink-500 to-pink-600 rounded-lg flex items-center justify-center">
                                        <ImageIcon className="w-4 h-4 text-white" />
                                    </div>
                                    <h4 className="text-lg font-semibold text-white">Imagens Adicionais</h4>
                                </div>
                                <button 
                                    type="button" 
                                    onClick={() => addExtraImage(product.id)} 
                                    className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-black bg-gradient-to-r from-pink-400 to-pink-500 rounded-xl hover:from-pink-500 hover:to-pink-600 transition-all duration-300 transform hover:scale-[1.02] shadow-lg"
                                >
                                    <Plus size={16} />Adicionar Imagem
                                </button>
                            </div>
                            <div className="space-y-4">{product.imagens.extra.map((img, imgIndex) => (<div key={img.id} className="flex items-end gap-3"><div className="flex-grow"><ImageUploadField label={`Imagem Extra ${imgIndex + 1}`} id={`img-extra-${img.id}`} onImageChange={(file) => handleExtraImageChange(product.id, img.id, file)} /></div><button type="button" onClick={() => removeExtraImage(product.id, img.id)} className="p-2 mb-1 text-red-400 hover:text-red-200 hover:bg-red-500/20 rounded-full transition-all duration-300"><Trash2 size={18} /></button></div>))}</div>
                        </div>
                    </div>
                </div>
                </div>
            </div>
        </div>
    );
};

function CriarListing() {
    const [selectedFile, setSelectedFile] = useState(null);
    const [amazonTemplate, setAmazonTemplate] = useState(null);
    const [products, setProducts] = useState([createNewProduct()]);
    const [isLoading, setIsLoading] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('');
    const [loadingProgress, setLoadingProgress] = useState(0);
    const [pollingIntervalId, setPollingIntervalId] = useState(null);
    
    const location = useLocation();
    const navigate = useNavigate();
    const { showSuccess, showError, showWarning, showInfo } = useNotification();

    useEffect(() => {
        if (location.state && location.state.products) {
            const productsFromState = location.state.products.map((p, index) => createNewProduct(p, index));
            setProducts(productsFromState);
            navigate(location.pathname, { replace: true, state: {} });
        }
    }, [location, navigate]);

    useEffect(() => {
        return () => {
            if (pollingIntervalId) {
                clearInterval(pollingIntervalId);
            }
        };
    }, [pollingIntervalId]);

    const updateProductState = (productId, updateCallback) => { setProducts(prev => prev.map(p => p.id === productId ? updateCallback(p) : p)); };
    const handleProductChange = (id, event) => { const { name, value } = event.target; updateProductState(id, p => ({ ...p, [name]: value })); };
    const addVariation = (productId) => updateProductState(productId, p => ({ ...p, variacoes: [...p.variacoes, createNewVariation()] }));
    const removeVariation = (productId, variationId) => updateProductState(productId, p => ({ ...p, variacoes: p.variacoes.filter(v => v.id !== variationId) }));
    const handleVariationChange = (productId, variationId, event) => { const { name, value } = event.target; updateProductState(productId, p => ({ ...p, variacoes: p.variacoes.map(v => v.id === variationId ? { ...v, [name]: value } : v) })); };
    const handleImageChange = (productId, imageType, file) => updateProductState(productId, p => ({ ...p, imagens: { ...p.imagens, [imageType]: file } }));
    const addExtraImage = (productId) => updateProductState(productId, p => ({ ...p, imagens: { ...p.imagens, extra: [...p.imagens.extra, createNewExtraImage()] } }));
    const removeExtraImage = (productId, imageId) => updateProductState(productId, p => ({ ...p, imagens: { ...p.imagens, extra: p.imagens.extra.filter(img => img.id !== imageId) } }));
    const handleExtraImageChange = (productId, imageId, file) => { updateProductState(productId, p => ({ ...p, imagens: { ...p.imagens, extra: p.imagens.extra.map(img => img.id === imageId ? { ...img, file: file } : img) } })); };

    const handleUploadSubmit = async () => {
        if (!selectedFile) {
            showWarning('Por favor, selecione um arquivo de planilha.');
            return;
        }
        
        setIsLoading(true);
        setLoadingMessage('Enviando planilha de produtos...');
        setLoadingProgress(20);
        
        const formData = new FormData();
        formData.append('planilha', selectedFile);
        
        try {
            setLoadingMessage('Processando dados da planilha...');
            setLoadingProgress(60);
            
            const response = await api.post('/upload-planilha/', formData, { 
                headers: { 'Content-Type': 'multipart/form-data' } 
            });
            
            setLoadingMessage('Finalizando carregamento...');
            setLoadingProgress(90);
            
            const productsFromApi = response.data.map((p, index) => createNewProduct(p, index));
            setProducts(productsFromApi.length > 0 ? productsFromApi : [createNewProduct()]);
            
            setLoadingProgress(100);
            showSuccess(`${productsFromApi.length} produtos carregados com sucesso!`, 'Planilha Processada');
            
        } catch (error) {
            console.error("Erro no upload da planilha de produtos:", error);
            const errorMessage = error.response?.data?.detail || error.message || 'Erro desconhecido';
            showError(`Falha ao processar planilha: ${errorMessage}`, 'Erro no Upload');
        } finally {
            setIsLoading(false);
            setLoadingProgress(0);
        }
    };

    const pollTaskStatus = (taskId) => {
        const intervalId = setInterval(async () => {
            try {
                const { data } = await api.get(`/task-status/${taskId}/`);
                
                if (data.status === 'SUCCESS') {
                    clearInterval(intervalId);
                    setPollingIntervalId(null);
                    
                    const fileContent = data.result.file_content;
                    const fileName = data.result.filename;
                    downloadBase64File(fileContent, fileName);
                    
                    setIsLoading(false);
                    setLoadingProgress(100);
                    showSuccess('Download iniciado automaticamente!', 'Planilha Gerada');
                    
                } else if (data.status === 'FAILURE') {
                    clearInterval(intervalId);
                    setPollingIntervalId(null);
                    setIsLoading(false);
                    
                    const errorDetail = data.result?.error || 'Erro desconhecido durante o processamento';
                    showError(`Falha na geração: ${errorDetail}`, 'Erro no Processamento');
                    
                } else if (data.status === 'PROGRESS') {
                    const meta = data.result;
                    if (meta && meta.step) {
                        const progressMessage = `${meta.step} ${meta.current && meta.total ? `(${meta.current} de ${meta.total})` : ''}`;
                        setLoadingMessage(progressMessage);
                        
                        // Calcular progresso baseado nos dados disponíveis
                        if (meta.current && meta.total) {
                            const progress = Math.round((meta.current / meta.total) * 80) + 10; // 10-90%
                            setLoadingProgress(progress);
                        }
                    }
                }
            } catch (error) {
                clearInterval(intervalId);
                setPollingIntervalId(null);
                setIsLoading(false);
                
                console.error('Erro ao consultar status da tarefa:', error);
                const errorMessage = error.response?.data?.detail || error.message || 'Erro de conexão';
                showError(`Falha na consulta: ${errorMessage}`, 'Erro de Comunicação');
            }
        }, 3000);
        setPollingIntervalId(intervalId);
    };

    const handleFinalSubmit = async (e) => {
        e.preventDefault();
        
        // Validações
        if (!amazonTemplate) {
            showWarning('Por favor, envie o modelo de planilha da Amazon (.xlsm).', 'Template Necessário');
            return;
        }
        
        if (products.length === 0) {
            showWarning('Adicione pelo menos um produto antes de gerar a planilha.', 'Produtos Necessários');
            return;
        }
        
        // Verificar se produtos têm dados mínimos
        const invalidProducts = products.filter(p => !p.titulo || !p.sku);
        if (invalidProducts.length > 0) {
            showWarning('Alguns produtos estão sem título ou SKU. Verifique os dados.', 'Dados Incompletos');
            return;
        }
        
        setIsLoading(true);
        setLoadingMessage('Preparando dados para envio...');
        setLoadingProgress(10);
        
        const formData = new FormData();
        const productsDataOnly = products.map(p => { const { imagens, ...rest } = p; return rest; });
        formData.append('products_data', JSON.stringify(productsDataOnly));
        formData.append('amazon_template', amazonTemplate);

        setLoadingMessage('Processando imagens...');
        setLoadingProgress(30);
        
        // Adicionar imagens
        products.forEach((p, productIndex) => {
            if (p.imagens.principal) formData.append(`imagem_p${productIndex}_principal`, p.imagens.principal);
            if (p.imagens.amostra) formData.append(`imagem_p${productIndex}_amostra`, p.imagens.amostra);
            p.imagens.extra.forEach((img, extraIndex) => { 
                if (img.file) formData.append(`imagem_p${productIndex}_extra_${extraIndex}`, img.file); 
            });
        });

        try {
            setLoadingMessage('Enviando dados para o servidor...');
            setLoadingProgress(50);
            
            const response = await api.post('/gerar-planilha/', formData, { 
                headers: { 'Content-Type': 'multipart/form-data' } 
            });
            
            const { task_id } = response.data;
            setLoadingMessage('Processamento iniciado! Aguardando resultado...');
            setLoadingProgress(60);
            
            showInfo('Processamento em andamento. Aguarde...', 'Gerando Planilha');
            pollTaskStatus(task_id);
            
        } catch (error) {
            console.error("Erro ao iniciar a geração da planilha:", error);
            const errorMessage = error.response?.data?.detail || error.message || 'Erro desconhecido';
            showError(`Falha ao iniciar geração: ${errorMessage}`, 'Erro no Envio');
            setIsLoading(false);
            setLoadingProgress(0);
        }
    };

    return (
        <div>
            <LoadingScreen 
                isVisible={isLoading}
                message={loadingMessage}
                showProgress={true}
                progress={loadingProgress}
                showTimer={true}
            />

            <div className="mb-8">
                <div className="flex items-center space-x-3 mb-2">
                    <div className="w-8 h-8 bg-gradient-to-r from-amber-400 to-amber-500 rounded-full flex items-center justify-center text-black font-bold shadow-lg">1</div>
                    <h1 className="text-3xl font-bold text-white">Envie suas planilhas</h1>
                </div>
                <p className="text-gray-400 ml-11">Faça upload dos arquivos necessários para começar o processamento</p>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
                <div className="group bg-gradient-to-br from-gray-800/80 to-gray-900/80 backdrop-blur-sm rounded-2xl border border-amber-500/20 hover:border-amber-500/40 transition-all duration-300 hover:shadow-2xl hover:shadow-amber-500/10">
                    <div className="p-8">
                        <div className="flex items-center space-x-3 mb-4">
                            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                                <FileText className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-white">Planilha de Produtos</h2>
                                <p className="text-sm text-gray-400">Dados dos seus produtos</p>
                            </div>
                        </div>
                        
                        <p className="text-gray-300 mb-6 leading-relaxed">
                            Envie a planilha com os dados dos produtos que você quer enriquecer. 
                            A IA irá processar estas informações automaticamente.
                        </p>
                        
                        <div className="bg-black/30 backdrop-blur-sm p-6 rounded-xl border border-gray-700/50 mb-6">
                            <label htmlFor="planilha_produtos" className="block mb-3 text-sm font-medium text-gray-300">
                                Arquivo de Produtos (.xlsx)
                            </label>
                            <div className="relative">
                                <input 
                                    type="file" 
                                    name="planilha_produtos" 
                                    id="planilha_produtos" 
                                    className="block w-full text-sm text-gray-300 file:mr-4 file:py-3 file:px-6 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-gradient-to-r file:from-amber-500/20 file:to-amber-400/20 file:text-amber-300 hover:file:from-amber-500/30 hover:file:to-amber-400/30 file:transition-all file:duration-300" 
                                    onChange={(e) => setSelectedFile(e.target.files[0])} 
                                />
                                {selectedFile && (
                                    <div className="mt-3 flex items-center space-x-2 text-xs text-green-400">
                                        <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                                        <span>Arquivo selecionado: {selectedFile.name}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                        
                        <button 
                            type="button" 
                            onClick={handleUploadSubmit} 
                            className="w-full px-6 py-4 font-bold text-black bg-gradient-to-r from-amber-400 to-amber-500 rounded-xl hover:from-amber-500 hover:to-amber-600 disabled:from-gray-600 disabled:to-gray-700 disabled:text-gray-400 transition-all duration-300 transform hover:scale-[1.02] disabled:hover:scale-100 shadow-lg hover:shadow-xl" 
                            disabled={!selectedFile || isLoading}
                        >
                            {isLoading ? 'Processando...' : 'Carregar Produtos'}
                        </button>
                    </div>
                </div>
                
                <div className="group bg-gradient-to-br from-gray-800/80 to-gray-900/80 backdrop-blur-sm rounded-2xl border border-amber-500/20 hover:border-amber-500/40 transition-all duration-300 hover:shadow-2xl hover:shadow-amber-500/10">
                    <div className="p-8">
                        <div className="flex items-center space-x-3 mb-4">
                            <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl flex items-center justify-center">
                                <Package className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-white">Modelo da Amazon</h2>
                                <p className="text-sm text-gray-400">Template .xlsm</p>
                            </div>
                        </div>
                        
                        <p className="text-gray-300 mb-6 leading-relaxed">
                            Faça o upload do seu arquivo de modelo da Amazon (.xlsm). 
                            Este arquivo será preenchido automaticamente.
                        </p>
                        
                        <div className="bg-black/30 backdrop-blur-sm p-8 rounded-xl border-2 border-dashed border-gray-600/50 hover:border-amber-500/50 transition-all duration-300 text-center group-hover:border-amber-500/30">
                            <UploadCloud className="w-16 h-16 text-gray-500 mx-auto mb-4 group-hover:text-amber-400 transition-colors duration-300" />
                            
                            <label htmlFor="amazon_template_upload" className="relative cursor-pointer">
                                <div className="bg-gradient-to-r from-amber-500/20 to-amber-400/20 hover:from-amber-500/30 hover:to-amber-400/30 text-amber-300 font-semibold rounded-xl px-6 py-3 text-sm transition-all duration-300 inline-block">
                                    {amazonTemplate ? 'Arquivo Selecionado' : 'Selecionar Modelo'}
                                </div>
                                <input 
                                    id="amazon_template_upload" 
                                    name="amazon_template_upload" 
                                    type="file" 
                                    className="sr-only" 
                                    accept=".xlsm" 
                                    onChange={(e) => setAmazonTemplate(e.target.files[0])} 
                                />
                            </label>
                            
                            {amazonTemplate && (
                                <div className="mt-4 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                                    <p className="text-sm text-green-400 font-medium">
                                        {amazonTemplate.name.length > 25
                                            ? `${amazonTemplate.name.substring(0, 25)}...` 
                                            : amazonTemplate.name
                                        }
                                    </p>
                                    <p className="text-xs text-gray-400 mt-1">
                                        {(amazonTemplate.size / 1024 / 1024).toFixed(2)} MB
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
            
            <form onSubmit={handleFinalSubmit}>
                <div className="mb-8">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-gradient-to-r from-amber-400 to-amber-500 rounded-full flex items-center justify-center text-black font-bold shadow-lg">2</div>
                            <h1 className="text-3xl font-bold text-white">Valide ou Edite os dados</h1>
                        </div>
                        <button type="button" onClick={() => setProducts(prev => [...prev, createNewProduct({}, prev.length)])} className="flex items-center gap-2 px-6 py-3 text-sm font-bold text-black bg-gradient-to-r from-amber-400 to-amber-500 rounded-xl hover:from-amber-500 hover:to-amber-600 transition-all duration-300 transform hover:scale-[1.02] shadow-lg"><Plus size={18} />Adicionar Produto</button>
                    </div>
                    <p className="text-gray-400 ml-11">Configure e valide os dados dos seus produtos</p>
                </div>

                <div className="space-y-6">
                    {products.map((product, index) => (
                        <ProductForm
                            key={product.id}
                            product={product}
                            index={index}
                            removeProduct={(id) => setProducts(prev => prev.filter(p => p.id !== id))}
                            handleProductChange={handleProductChange}
                            addVariation={addVariation}
                            removeVariation={removeVariation}
                            handleVariationChange={handleVariationChange}
                            handleImageChange={handleImageChange}
                            addExtraImage={addExtraImage}
                            removeExtraImage={removeExtraImage}
                            handleExtraImageChange={handleExtraImageChange}
                        />
                    ))}
                </div>
                
                <div className="mt-16 flex justify-center">
                    <div className="text-center">
                        <div className="flex items-center justify-center space-x-3 mb-6">
                            <div className="w-8 h-8 bg-gradient-to-r from-amber-400 to-amber-500 rounded-full flex items-center justify-center text-black font-bold shadow-lg">3</div>
                            <h2 className="text-3xl font-bold text-white">Gere sua planilha final</h2>
                        </div>
                        <p className="text-gray-400 mb-8">Finalize o processo e baixe sua planilha preenchida</p>
                        <button 
                            type="submit" 
                            className="px-16 py-5 font-bold text-black bg-gradient-to-r from-amber-400 to-amber-500 rounded-2xl hover:from-amber-500 hover:to-amber-600 disabled:from-gray-600 disabled:to-gray-700 disabled:text-gray-400 transition-all duration-300 transform hover:scale-[1.02] disabled:hover:scale-100 shadow-2xl hover:shadow-amber-500/25 text-xl" 
                            disabled={isLoading || products.length === 0 || !amazonTemplate}
                        >
                            {isLoading ? 'Processando...' : 'Gerar Planilha Final'}
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
}

export default CriarListing;
