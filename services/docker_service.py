import docker
import os
import tempfile
import shutil
import gzip
from urllib.parse import urlparse
from config import Config
from utils.logger import setup_logger

logger = setup_logger('docker_service')

class DockerService:
    """Docker 服务类"""
    
    def __init__(self):
        try:
            self.client = docker.from_env(timeout=Config.DOCKER_TIMEOUT)
            logger.info("Docker 客户端初始化成功")
        except Exception as e:
            logger.error(f"Docker 客户端初始化失败: {str(e)}")
            raise Exception("无法连接到 Docker，请确保 Docker 服务已启动")
    
    def ping(self):
        """检查 Docker 连接"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Docker ping 失败: {str(e)}")
            return False
    
    def login(self, registry, username, password):
        """登录到 registry"""
        try:
            logger.info(f"登录到 registry: {registry}")
            self.client.login(
                username=username,
                password=password,
                registry=registry
            )
            return True
        except Exception as e:
            logger.error(f"登录失败: {str(e)}")
            raise Exception(f"Docker login 失败: {str(e)}")
    
    def pull_image(self, image_name, tag='latest'):
        """拉取镜像"""
        try:
            full_image = f"{image_name}:{tag}"
            logger.info(f"开始拉取镜像: {full_image}")
            
            image = self.client.images.pull(image_name, tag=tag)
            logger.info(f"镜像拉取成功: {image.tags}")
            
            return image
        except docker.errors.ImageNotFound:
            raise Exception(f"镜像不存在: {image_name}:{tag}")
        except docker.errors.APIError as e:
            logger.error(f"拉取镜像失败: {str(e)}")
            raise Exception(f"拉取镜像失败: {str(e)}")
    
    def save_and_compress_image(self, image, output_gz_path):
        """保存镜像并直接压缩为 tar.gz"""
        try:
            logger.info(f"正在拉取并压缩镜像到: {output_gz_path}")
            
            # 使用 gzip 打开文件进行写入
            with gzip.open(output_gz_path, 'wb') as f_out:
                for chunk in image.save(named=True):
                    f_out.write(chunk)
            
            file_size = os.path.getsize(output_gz_path)
            logger.info(f"镜像保存并压缩成功，大小: {file_size / 1024 / 1024:.2f} MB")
            
            return output_gz_path
        except Exception as e:
            logger.error(f"保存压缩镜像失败: {str(e)}")
            raise Exception(f"保存压缩镜像失败: {str(e)}")

    def download_image(self, harbor_url, username, password, image_name, tag='latest'):
        """完整的镜像下载流程"""
        temp_dir = None
        
        try:
            # 解析 registry 地址
            parsed = urlparse(harbor_url)
            registry = parsed.netloc or parsed.path
            
            # 登录
            self.login(registry, username, password)
            
            # 构建完整镜像名
            full_image_name = f"{registry}/{image_name}"
            
            # 拉取镜像
            image = self.pull_image(full_image_name, tag)
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(dir=Config.DOWNLOAD_FOLDER)
            
            # 生成文件名
            safe_name = f"{image_name.replace('/', '_')}_{tag}"
            gz_path = os.path.join(temp_dir, f"{safe_name}.tar.gz")
            
            # 保存并压缩镜像
            final_path = self.save_and_compress_image(image, gz_path)
            
            return {
                'path': final_path,
                'filename': os.path.basename(final_path),
                'size': os.path.getsize(final_path),
                'image': f"{full_image_name}:{tag}"
            }
            
        except Exception as e:
            # 清理临时文件
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise e
    
    def get_local_images(self):
        """获取本地镜像列表"""
        try:
            images = self.client.images.list()
            return [{
                'id': img.short_id,
                'tags': img.tags,
                'size': img.attrs['Size'],
                'created': img.attrs['Created']
            } for img in images]
        except Exception as e:
            logger.error(f"获取本地镜像失败: {str(e)}")
            raise Exception(f"获取本地镜像失败: {str(e)}")
    
    def remove_image(self, image_id):
        """删除本地镜像"""
        try:
            self.client.images.remove(image_id, force=True)
            logger.info(f"镜像已删除: {image_id}")
            return True
        except Exception as e:
            logger.error(f"删除镜像失败: {str(e)}")
            raise Exception(f"删除镜像失败: {str(e)}")
    
    def upload_image(self, harbor_url, username, password, target_project, tar_file_path):
        """上传镜像到 Harbor"""
        temp_dir = None
        
        try:
            parsed = urlparse(harbor_url)
            registry = parsed.netloc or parsed.path
            
            logger.info(f"开始上传镜像: {tar_file_path} 到 {registry}/{target_project}")
            
            self.login(registry, username, password)
            
            logger.info(f"正在加载镜像文件: {tar_file_path}")
            with open(tar_file_path, 'rb') as f:
                images = self.client.images.load(f)
            
            if not images:
                raise Exception("无法从文件中加载镜像，请检查文件格式")
            
            uploaded_images = []
            for image in images:
                if not image.tags:
                    raise Exception("镜像没有标签信息，无法上传。请使用 docker tag 命令为镜像添加标签后重新保存")
                
                original_tag = image.tags[0]
                logger.info(f"原始镜像标签: {original_tag}")
                
                parts = original_tag.split('/')
                if ':' in parts[-1]:
                    image_name, tag = parts[-1].rsplit(':', 1)
                else:
                    image_name = parts[-1]
                    tag = 'latest'
                    logger.info(f"镜像没有标签，使用默认标签: latest")
                
                if not image_name:
                    raise Exception("无法解析镜像名称，请检查镜像文件")
                
                new_tag = f"{registry}/{target_project}/{image_name}:{tag}"
                logger.info(f"重新标记镜像: {original_tag} -> {new_tag}")
                
                image.tag(new_tag)
                
                logger.info(f"开始推送镜像: {new_tag}")
                push_result = self.client.images.push(new_tag, stream=True, decode=True)
                
                for line in push_result:
                    if 'error' in line:
                        error_msg = line.get('error', '未知错误')
                        if 'denied' in error_msg.lower() or 'unauthorized' in error_msg.lower():
                            raise Exception(f"没有权限上传到项目 {target_project}，请检查用户权限")
                        if 'name unknown' not in error_msg.lower():
                            raise Exception(f"推送镜像失败: {error_msg}")
                    if 'status' in line:
                        status_msg = line.get('status', '')
                        try:
                            logger.info(f"推送进度: {status_msg}")
                        except UnicodeEncodeError:
                            logger.info(f"推送进度: [编码错误]")
                
                logger.info(f"镜像上传成功: {new_tag}")
                uploaded_images.append({
                    'original': original_tag,
                    'uploaded': new_tag,
                    'image_name': image_name,
                    'tag': tag
                })
                
                try:
                    self.client.images.remove(new_tag, force=True)
                    logger.info(f"已清理本地镜像: {new_tag}")
                except Exception as e:
                    logger.warning(f"清理本地镜像失败: {str(e)}")
            
            return {
                'success': True,
                'uploaded_images': uploaded_images,
                'target_registry': registry,
                'target_project': target_project
            }
            
        except Exception as e:
            logger.error(f"上传镜像失败: {str(e)}")
            raise e
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)