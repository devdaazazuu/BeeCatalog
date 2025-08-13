import React, { useState, useEffect } from 'react';
import { Settings, History, Database, Trash2, CheckCircle, Search, Filter, Calendar, FileSpreadsheet, Link, User, AlertCircle, TrendingUp } from 'lucide-react';
import { useOutletContext } from 'react-router-dom';

const Configuracoes = () => {
  const [activeTab, setActiveTab] = useState('historico');
  const [historyData, setHistoryData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({});
  const [filters, setFilters] = useState({
    search: '',
    status: 'all',
    origin: 'all',
    dateFrom: '',
    dateTo: ''
  });
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
    itemsPerPage: 20
  });
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [productToDelete, setProductToDelete] = useState(null);
  
  const { notifications } = useOutletContext();

  // Carregar dados do histórico
  const loadHistoryData = async (page = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: (pagination?.itemsPerPage || 20).toString(),
        ...filters
      });
      
      const response = await fetch(`http://localhost:8000/api/history/?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setHistoryData(data.data.products);
        setPagination(data.data.pagination);
        setStats(data.data.statistics);
      } else {
        notifications.removeNotification('error', data.error || 'Erro ao carregar histórico');
      }
    } catch (error) {
      console.error('Erro ao carregar histórico:', error);
      notifications.removeNotification('error', 'Erro de conexão ao carregar histórico');
    } finally {
      setLoading(false);
    }
  };

  // Validar produto
  const validateProduct = async (productId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/memory/validate/${productId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const data = await response.json();
      
      if (data.success) {
        notifications.removeNotification('success', 'Produto validado com sucesso!');
        loadHistoryData(pagination?.currentPage || 1);
      } else {
        notifications.removeNotification('error', data.error || 'Erro ao validar produto');
      }
    } catch (error) {
      console.error('Erro ao validar produto:', error);
      notifications.removeNotification('error', 'Erro de conexão ao validar produto');
    }
  };

  // Excluir produto
  const deleteProduct = async (productId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/memory/delete/${productId}/`, {
        method: 'DELETE',
      });
      
      const data = await response.json();
      
      if (data.success) {
        notifications.removeNotification('success', 'Produto excluído com sucesso!');
        loadHistoryData(pagination?.currentPage || 1);
        setShowDeleteModal(false);
        setProductToDelete(null);
      } else {
        notifications.removeNotification('error', data.error || 'Erro ao excluir produto');
      }
    } catch (error) {
      console.error('Erro ao excluir produto:', error);
      notifications.removeNotification('error', 'Erro de conexão ao excluir produto');
    }
  };

  // Aplicar filtros
  const applyFilters = () => {
    loadHistoryData(1);
  };

  // Limpar filtros
  const clearFilters = () => {
    setFilters({
      search: '',
      status: 'all',
      origin: 'all',
      dateFrom: '',
      dateTo: ''
    });
  };

  // Carregar dados iniciais
  useEffect(() => {
    if (activeTab === 'historico') {
      loadHistoryData();
    }
  }, [activeTab]);

  // Função para obter ícone da origem
  const getOriginIcon = (origin) => {
    switch (origin) {
      case 'spreadsheet':
        return <FileSpreadsheet size={16} className="text-green-400" />;
      case 'link_extraction':
        return <Link size={16} className="text-blue-400" />;
      case 'manual':
        return <User size={16} className="text-purple-400" />;
      default:
        return <AlertCircle size={16} className="text-gray-400" />;
    }
  };

  // Função para obter texto da origem
  const getOriginText = (origin) => {
    switch (origin) {
      case 'spreadsheet':
        return 'Planilha';
      case 'link_extraction':
        return 'Extração de Link';
      case 'manual':
        return 'Manual';
      default:
        return 'Desconhecido';
    }
  };

  // Função para obter cor do status
  const getStatusColor = (status) => {
    switch (status) {
      case 'validated':
        return 'text-green-400 bg-green-400/10';
      case 'pending':
        return 'text-yellow-400 bg-yellow-400/10';
      case 'error':
        return 'text-red-400 bg-red-400/10';
      default:
        return 'text-gray-400 bg-gray-400/10';
    }
  };

  // Função para formatar data
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Data inválida';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-amber-500 rounded-xl flex items-center justify-center">
              <Settings className="w-6 h-6 text-slate-900" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Configurações</h1>
              <p className="text-slate-400">Gerencie o histórico e configurações do sistema</p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-8">
          <div className="flex space-x-1 bg-slate-800/50 p-1 rounded-xl border border-slate-700">
            <button
              onClick={() => setActiveTab('historico')}
              className={`flex items-center space-x-2 px-6 py-3 rounded-lg transition-all duration-300 ${
                activeTab === 'historico'
                  ? 'bg-gradient-to-r from-amber-500 to-amber-400 text-slate-900 shadow-lg'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <History size={20} />
              <span className="font-medium">Histórico de Catalogação</span>
            </button>
            <button
              onClick={() => setActiveTab('sistema')}
              className={`flex items-center space-x-2 px-6 py-3 rounded-lg transition-all duration-300 ${
                activeTab === 'sistema'
                  ? 'bg-gradient-to-r from-amber-500 to-amber-400 text-slate-900 shadow-lg'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <Database size={20} />
              <span className="font-medium">Sistema</span>
            </button>
          </div>
        </div>

        {/* Conteúdo das Tabs */}
        {activeTab === 'historico' && (
          <div className="space-y-6">
            {/* Estatísticas */}
            {stats && Object.keys(stats).length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-400 text-sm">Total de Produtos</p>
                      <p className="text-2xl font-bold text-white">{stats.total_products || 0}</p>
                    </div>
                    <Database className="w-8 h-8 text-amber-400" />
                  </div>
                </div>
                
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-400 text-sm">Validados</p>
                      <p className="text-2xl font-bold text-green-400">{stats.by_status?.validated || 0}</p>
                    </div>
                    <CheckCircle className="w-8 h-8 text-green-400" />
                  </div>
                </div>
                
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-400 text-sm">De Planilhas</p>
                      <p className="text-2xl font-bold text-blue-400">{stats.by_origin?.spreadsheet || 0}</p>
                    </div>
                    <FileSpreadsheet className="w-8 h-8 text-blue-400" />
                  </div>
                </div>
                
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-400 text-sm">Qualidade Média</p>
                      <p className="text-2xl font-bold text-amber-400">{stats.average_quality_score || 0}%</p>
                    </div>
                    <TrendingUp className="w-8 h-8 text-amber-400" />
                  </div>
                </div>
              </div>
            )}

            {/* Filtros */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                <Filter size={20} className="text-amber-400" />
                <span>Filtros</span>
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                {/* Busca */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Buscar</label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={16} />
                    <input
                      type="text"
                      value={filters.search}
                      onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                      placeholder="Nome ou SKU..."
                      className="w-full pl-10 pr-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Status */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Status</label>
                  <select
                    value={filters.status}
                    onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                  >
                    <option value="all">Todos</option>
                    <option value="validated">Validados</option>
                    <option value="pending">Pendentes</option>
                  </select>
                </div>

                {/* Origem */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Origem</label>
                  <select
                    value={filters.origin}
                    onChange={(e) => setFilters({ ...filters, origin: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                  >
                    <option value="all">Todas</option>
                    <option value="spreadsheet">Planilha</option>
                    <option value="manual">Manual</option>
                    <option value="link_extraction">Extração de Link</option>
                  </select>
                </div>

                {/* Data Inicial */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Data Inicial</label>
                  <input
                    type="date"
                    value={filters.dateFrom}
                    onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                  />
                </div>

                {/* Data Final */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Data Final</label>
                  <input
                    type="date"
                    value={filters.dateTo}
                    onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="flex space-x-4 mt-4">
                <button
                  onClick={applyFilters}
                  className="px-6 py-2 bg-gradient-to-r from-amber-500 to-amber-400 text-slate-900 rounded-lg font-medium hover:from-amber-600 hover:to-amber-500 transition-all duration-300"
                >
                  Aplicar Filtros
                </button>
                <button
                  onClick={clearFilters}
                  className="px-6 py-2 bg-slate-700 text-white rounded-lg font-medium hover:bg-slate-600 transition-all duration-300"
                >
                  Limpar
                </button>
              </div>
            </div>

            {/* Tabela de Histórico */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
              <div className="p-6 border-b border-slate-700">
                <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
                  <History size={20} className="text-amber-400" />
                  <span>Histórico de Catalogação</span>
                </h3>
              </div>

              {loading ? (
                <div className="p-8 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-400 mx-auto"></div>
                  <p className="text-slate-400 mt-2">Carregando histórico...</p>
                </div>
              ) : historyData.length === 0 ? (
                <div className="p-8 text-center">
                  <Database className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400">Nenhum produto encontrado no histórico</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-700/50">
                      <tr>
                        <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Produto</th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Data</th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Origem</th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Qualidade</th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Ações</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                      {historyData.map((product, index) => (
                        <tr key={product.id || index} className="hover:bg-slate-700/30 transition-colors duration-200">
                          <td className="px-6 py-4">
                            <div>
                              <div className="text-sm font-medium text-white">{product.name}</div>
                              {product.sku && (
                                <div className="text-sm text-slate-400">SKU: {product.sku}</div>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-300">
                            {formatDate(product.created_at)}
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center space-x-2">
                              {getOriginIcon(product.origin)}
                              <span className="text-sm text-slate-300">{getOriginText(product.origin)}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(product.status)}`}>
                              {product.status === 'validated' ? 'Validado' : 'Pendente'}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center space-x-2">
                              <div className="w-16 bg-slate-700 rounded-full h-2">
                                <div 
                                  className="bg-gradient-to-r from-amber-500 to-amber-400 h-2 rounded-full transition-all duration-300"
                                  style={{ width: `${product.data_quality_score || 0}%` }}
                                ></div>
                              </div>
                              <span className="text-sm text-slate-300">{product.data_quality_score || 0}%</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center space-x-2">
                              {product.status !== 'validated' && (
                                <button
                                  onClick={() => validateProduct(product.id)}
                                  className="p-2 text-green-400 hover:text-green-300 hover:bg-green-400/10 rounded-lg transition-all duration-200"
                                  title="Validar produto"
                                >
                                  <CheckCircle size={16} />
                                </button>
                              )}
                              <button
                                onClick={() => {
                                  setProductToDelete(product);
                                  setShowDeleteModal(true);
                                }}
                                className="p-2 text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded-lg transition-all duration-200"
                                title="Excluir produto"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Paginação */}
              {(pagination?.totalPages || 0) > 1 && (
                <div className="px-6 py-4 border-t border-slate-700 flex items-center justify-between">
                  <div className="text-sm text-slate-400">
                    Mostrando {(((pagination?.currentPage || 1) - 1) * (pagination?.itemsPerPage || 20)) + 1} a {Math.min((pagination?.currentPage || 1) * (pagination?.itemsPerPage || 20), pagination?.totalItems || 0)} de {pagination?.totalItems || 0} produtos
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => loadHistoryData((pagination?.currentPage || 1) - 1)}
                      disabled={!pagination?.hasPrevious}
                      className="px-3 py-1 text-sm bg-slate-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600 transition-colors duration-200"
                    >
                      Anterior
                    </button>
                    <span className="text-sm text-slate-300">
                      Página {pagination?.currentPage || 1} de {pagination?.totalPages || 1}
                    </span>
                    <button
                      onClick={() => loadHistoryData((pagination?.currentPage || 1) + 1)}
                      disabled={!pagination?.hasNext}
                      className="px-3 py-1 text-sm bg-slate-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600 transition-colors duration-200"
                    >
                      Próxima
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab Sistema */}
        {activeTab === 'sistema' && (
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Configurações do Sistema</h3>
            <p className="text-slate-400">Configurações do sistema serão implementadas em versões futuras.</p>
          </div>
        )}
      </div>

      {/* Modal de Confirmação de Exclusão */}
      {showDeleteModal && productToDelete && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 max-w-md w-full">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-red-500/20 rounded-lg flex items-center justify-center">
                <Trash2 className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Confirmar Exclusão</h3>
                <p className="text-sm text-slate-400">Esta ação não pode ser desfeita</p>
              </div>
            </div>
            
            <p className="text-slate-300 mb-6">
              Tem certeza que deseja excluir o produto <strong>{productToDelete.name}</strong>? 
              Todos os dados associados serão removidos permanentemente.
            </p>
            
            <div className="flex space-x-3">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setProductToDelete(null);
                }}
                className="flex-1 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors duration-200"
              >
                Cancelar
              </button>
              <button
                onClick={() => deleteProduct(productToDelete.id)}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200"
              >
                Excluir
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Configuracoes;