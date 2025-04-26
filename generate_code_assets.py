import csv
import json
import random
import uuid
import datetime
from openai import OpenAI

# Set API key
client = OpenAI(api_key="")

# CSV file paths
ASSETS_CSV = "input/100_digital_bank_assets.csv"
TAGS_CSV = "input/20_digital_bank_tags.csv"
USERS_CSV = "input/10_digital_bank_users.csv"

# Output JSON file paths
CODE_ASSETS_JSON = "output/CodeAssets.json"
FILE_SYSTEM_NODES_JSON = "output/FileSystemNodes.json"

# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------
def generate_guid():
    return str(uuid.uuid4())

def to_folder_name(name):
    """Convert an asset name into a valid folder name (alphanumeric only)."""
    return "".join(c for c in name if c.isalnum())

def to_file_name(name):
    """Convert an asset name into a valid C# file name (append .cs)."""
    return to_folder_name(name) + ".cs"

def generate_project_structure(asset_name, asset_description, available_tags):
    """
    Use the ChatCompletion API with function calling to generate a multi-folder,
    multi-file C# project structure and recommended tags.
    
    The model is instructed to return a JSON object with the following format:
    
    {
      "projectStructure": {
         "rootFolderName": "<name>",
         "nodes": [
             // For a folder: {"type": "folder", "name": "<folderName>", "items": [ ... nodes ... ] },
             // For a file: {"type": "file", "name": "<fileName>", "code": "<code text>" }
         ]
      },
      "recommendedTags": [ "TagName1", "TagName2", ... ]
    }
    
    By using the function calling capability with a defined schema, we ensure the response is valid JSON.
    """
    # Define the function schema for the project structure.
    function_schema = {
        "name": "create_project_structure",
        "description": "Generates a multi-folder, multi-file C# project structure and recommended tags for a digital bank asset.",
        "parameters": {
            "type": "object",
            "properties": {
                "projectStructure": {
                    "type": "object",
                    "properties": {
                        "rootFolderName": {"type": "string", "description": "Name of the root folder"},
                        "nodes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["folder", "file"],
                                        "description": "Type of the node (folder or file)"
                                    },
                                    "name": {"type": "string", "description": "Name of the folder or file"},
                                    "code": {"type": "string", "description": "For files, the code content"},
                                    "items": {
                                        "type": "array",
                                        "description": "Child nodes (only for folders)",
                                        "items": {"type": "object"}
                                    }
                                },
                                "required": ["type", "name"]
                            }
                        }
                    },
                    "required": ["rootFolderName", "nodes"]
                },
                "recommendedTags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of recommended tag names selected from the available tags."
                }
            },
            "required": ["projectStructure", "recommendedTags"]
        }
    }

    available_tags_str = json.dumps(available_tags)
    user_message = """
Below are examples of correctly generated responses:

Example 1:
Input:
    Asset Name: Chat Support Integration
    Asset Description: Integrates live chat support into customer service platforms.
""" + f"""
    Available Tags (choose from these if applicable): {available_tags_str}
""" + """
    
Output:
{
  "projectStructure": {
    "rootFolderName": "ChatSupportIntegration",
    "nodes": [
      {
        "type": "file",
        "name": "Program.cs",
        "code": "using Microsoft.AspNetCore.Hosting;\nusing Microsoft.Extensions.Hosting;\n\nnamespace ChatSupportIntegration\n{\n    public class Program\n    {\n        public static void Main(string[] args)\n        {\n            CreateHostBuilder(args).Build().Run();\n        }\n\n        public static IHostBuilder CreateHostBuilder(string[] args) =>\n            Host.CreateDefaultBuilder(args)\n                .ConfigureWebHostDefaults(webBuilder =>\n                {\n                    webBuilder.UseStartup<Startup>();\n                });\n    }\n}",
      },
      {
        "type": "file",
        "name": "Startup.cs",
        "code": "using Microsoft.AspNetCore.Builder;\nusing Microsoft.AspNetCore.Hosting;\nusing Microsoft.Extensions.DependencyInjection;\nusing Microsoft.Extensions.Hosting;\nusing ChatSupportIntegration.Services;\nusing ChatSupportIntegration.Infrastructure;\n\nnamespace ChatSupportIntegration\n{\n    public class Startup\n    {\n        public void ConfigureServices(IServiceCollection services)\n        {\n            services.AddControllers();\n            services.AddHttpClient();\n            services.AddLogging();\n            services.AddSingleton<IChatService, ChatService>();\n            services.AddSingleton<IIntegrationService, IntegrationService>();\n            services.AddSingleton<IChatLogger, ChatLogger>();\n            services.AddSingleton<IIntegrationAdapter, IntegrationAdapter>();\n        }\n\n        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)\n        {\n            if (env.IsDevelopment())\n            {\n                app.UseDeveloperExceptionPage();\n            }\n            \n            app.UseRouting();\n\n            app.UseEndpoints(endpoints =>\n            {\n                endpoints.MapControllers();\n            });\n        }\n    }\n}\n",
      },
      {
        "type": "folder",
        "name": "Controllers",
        "items": [
          {
            "type": "file",
            "name": "ChatSupportController.cs",
            "code": "using Microsoft.AspNetCore.Mvc;\nusing System.Threading.Tasks;\nusing ChatSupportIntegration.Services;\nusing ChatSupportIntegration.Models;\n\nnamespace ChatSupportIntegration.Controllers\n{\n    [ApiController]\n    [Route(\"api/[controller]\")]\n    public class ChatSupportController : ControllerBase\n    {\n        private readonly IChatService _chatService;\n\n        public ChatSupportController(IChatService chatService)\n        {\n            _chatService = chatService;\n        }\n\n        [HttpGet(\"{sessionId}\")]\n        public async Task<ActionResult<ChatSession>> GetChatSession(string sessionId)\n        {\n            var session = await _chatService.GetChatSessionAsync(sessionId);\n            if (session == null) \n                return NotFound();\n            \n            return Ok(session);\n        }\n\n        [HttpPost]\n        public async Task<ActionResult<ChatMessage>> PostChatMessage([FromBody] ChatMessage message)\n        {\n            var processedMessage = await _chatService.ProcessChatMessageAsync(message);\n            return Ok(processedMessage);\n        }\n    }\n}\n",
          }
        ]
      },
      {
        "type": "folder",
        "name": "Services",
        "items": [
          {
            "type": "file",
            "name": "ChatService.cs",
            "code": "using System;\nusing System.Threading.Tasks;\nusing ChatSupportIntegration.Models;\nusing ChatSupportIntegration.Infrastructure;\n\nnamespace ChatSupportIntegration.Services\n{\n    public interface IChatService\n    {\n        Task<ChatSession> GetChatSessionAsync(string sessionId);\n        Task<ChatMessage> ProcessChatMessageAsync(ChatMessage message);\n    }\n\n    public class ChatService : IChatService\n    {\n        private readonly IIntegrationService _integrationService;\n        private readonly IChatLogger _chatLogger;\n\n        public ChatService(IIntegrationService integrationService, IChatLogger chatLogger)\n        {\n            _integrationService = integrationService;\n            _chatLogger = chatLogger;\n        }\n\n        // In a production environment, persistent storage like a database would be used.\n        private static readonly System.Collections.Concurrent.ConcurrentDictionary<string, ChatSession> Sessions =\n            new System.Collections.Concurrent.ConcurrentDictionary<string, ChatSession>();\n\n        public async Task<ChatSession> GetChatSessionAsync(string sessionId)\n        {\n            Sessions.TryGetValue(sessionId, out ChatSession session);\n            return await Task.FromResult(session);\n        }\n\n        public async Task<ChatMessage> ProcessChatMessageAsync(ChatMessage message)\n        {\n            if (string.IsNullOrEmpty(message.SessionId))\n            {\n                // Create a new session if none exists.\n                message.SessionId = Guid.NewGuid().ToString();\n                var newSession = new ChatSession { SessionId = message.SessionId };\n                Sessions.TryAdd(newSession.SessionId, newSession);\n            }\n\n            Sessions.AddOrUpdate(message.SessionId,\n                new ChatSession { SessionId = message.SessionId, Messages = new System.Collections.Generic.List<ChatMessage> { message } },\n                (key, existingSession) =>\n                {\n                    existingSession.Messages.Add(message);\n                    return existingSession;\n                });\n\n            _chatLogger.LogInfo($\"Processing message for session {message.SessionId}\");\n            \n            // Integrate with the external live chat provider\n            var response = await _integrationService.SendMessageToLiveChatAsync(message);\n            \n            if (response != null)\n            {\n                Sessions.AddOrUpdate(message.SessionId,\n                    new ChatSession { SessionId = message.SessionId, Messages = new System.Collections.Generic.List<ChatMessage> { response } },\n                    (key, existingSession) =>\n                    {\n                        existingSession.Messages.Add(response);\n                        return existingSession;\n                    });\n            }\n\n            return response ?? message;\n        }\n    }\n}\n",
          },
          {
            "type": "file",
            "name": "IntegrationService.cs",
            "code": "using System.Net.Http;\nusing System.Text.Json;\nusing System.Threading.Tasks;\nusing ChatSupportIntegration.Models;\nusing ChatSupportIntegration.Infrastructure;\n\nnamespace ChatSupportIntegration.Services\n{\n    public interface IIntegrationService\n    {\n        Task<ChatMessage> SendMessageToLiveChatAsync(ChatMessage message);\n    }\n\n    public class IntegrationService : IIntegrationService\n    {\n        private readonly HttpClient _httpClient;\n        private readonly IIntegrationAdapter _integrationAdapter;\n\n        public IntegrationService(IIntegrationAdapter integrationAdapter, IHttpClientFactory httpClientFactory)\n        {\n            _integrationAdapter = integrationAdapter;\n            _httpClient = httpClientFactory.CreateClient();\n        }\n\n        public async Task<ChatMessage> SendMessageToLiveChatAsync(ChatMessage message)\n        {\n            // Delegate the external communication to the adapter\n            return await _integrationAdapter.SendChatMessageAsync(message);\n        }\n    }\n}\n",
          }
        ]
      },
      {
        "type": "folder",
        "name": "Models",
        "items": [
          {
            "type": "file",
            "name": "ChatMessage.cs",
            "code": "using System;\n\nnamespace ChatSupportIntegration.Models\n{\n    public class ChatMessage\n    {\n        public string MessageId { get; set; } = Guid.NewGuid().ToString();\n        public string SessionId { get; set; }\n        public string UserId { get; set; }\n        public string Content { get; set; }\n        public DateTime Timestamp { get; set; } = DateTime.UtcNow;\n    }\n}\n",
          },
          {
            "type": "file",
            "name": "ChatSession.cs",
            "code": "using System.Collections.Generic;\n\nnamespace ChatSupportIntegration.Models\n{\n    public class ChatSession\n    {\n        public string SessionId { get; set; }\n        public List<ChatMessage> Messages { get; set; } = new List<ChatMessage>();\n    }\n}\n",
          }
        ]
      },
      {
        "type": "folder",
        "name": "Infrastructure",
        "items": [
          {
            "type": "file",
            "name": "ChatLogger.cs",
            "code": "using System;\nusing Microsoft.Extensions.Logging;\n\nnamespace ChatSupportIntegration.Infrastructure\n{\n    public interface IChatLogger\n    {\n        void LogInfo(string message);\n        void LogError(string message, Exception ex);\n    }\n\n    public class ChatLogger : IChatLogger\n    {\n        private readonly ILogger<ChatLogger> _logger;\n\n        public ChatLogger(ILogger<ChatLogger> logger)\n        {\n            _logger = logger;\n        }\n\n        public void LogInfo(string message)\n        {\n            _logger.LogInformation(message);\n        }\n\n        public void LogError(string message, Exception ex)\n        {\n            _logger.LogError(ex, message);\n        }\n    }\n}\n",
          },
          {
            "type": "file",
            "name": "IntegrationAdapter.cs",
            "code": "using System.Net.Http;\nusing System.Text;\nusing System.Text.Json;\nusing System.Threading.Tasks;\nusing ChatSupportIntegration.Models;\n\nnamespace ChatSupportIntegration.Infrastructure\n{\n    public interface IIntegrationAdapter\n    {\n        Task<ChatMessage> SendChatMessageAsync(ChatMessage message);\n    }\n\n    public class IntegrationAdapter : IIntegrationAdapter\n    {\n        private readonly HttpClient _httpClient;\n\n        public IntegrationAdapter(IHttpClientFactory httpClientFactory)\n        {\n            _httpClient = httpClientFactory.CreateClient();\n        }\n\n        public async Task<ChatMessage> SendChatMessageAsync(ChatMessage message)\n        {\n            // Replace with actual live chat provider endpoint in production\n            string externalEndpoint = \"https://api.livechatprovider.com/send\";\n            \n            var jsonContent = JsonSerializer.Serialize(message);\n            var content = new StringContent(jsonContent, Encoding.UTF8, \"application/json\");\n            \n            var response = await _httpClient.PostAsync(externalEndpoint, content);\n            response.EnsureSuccessStatusCode();\n\n            var responseContent = await response.Content.ReadAsStringAsync();\n            var chatResponse = JsonSerializer.Deserialize<ChatMessage>(responseContent, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });\n            return chatResponse;\n        }\n    }\n}\n",
          }
        ]
      }
    ]
  },
  "recommendedTags": [
    "Integration"
  ]
}

Example 2:
Input:
    Asset Name: Token Management System
    Asset Description: Manages the creation, validation, and storage of security tokens.
""" + f"""
    Available Tags (choose from these if applicable): {available_tags_str}
""" + """
    
Output:
{
  "projectStructure": {
    "rootFolderName": "TokenManagementSystem",
    "nodes": [
      {
        "type": "file",
        "name": "Program.cs",
        "code": "using Microsoft.AspNetCore.Builder;\nusing Microsoft.AspNetCore.Hosting;\nusing Microsoft.Extensions.DependencyInjection;\nusing Microsoft.Extensions.Hosting;\nusing TokenManagementSystem.Services;\nusing TokenManagementSystem.Data;\n\nnamespace TokenManagementSystem\n{\n    public class Program\n    {\n        public static void Main(string[] args)\n        {\n            var builder = WebApplication.CreateBuilder(args);\n            builder.Services.AddControllers();\n            builder.Services.AddSingleton<ITokenService, TokenService>();\n            builder.Services.AddSingleton<ITokenRepository, TokenRepository>();\n\n            var app = builder.Build();\n\n            app.UseRouting();\n            app.UseEndpoints(endpoints =>\n            {\n                endpoints.MapControllers();\n            });\n\n            app.Run();\n        }\n    }\n}\n",
      },
      {
        "type": "folder",
        "name": "Controllers",
        "items": [
          {
            "type": "file",
            "name": "TokenController.cs",
            "code": "using System;\nusing Microsoft.AspNetCore.Mvc;\nusing TokenManagementSystem.Models;\nusing TokenManagementSystem.Services;\n\nnamespace TokenManagementSystem.Controllers\n{\n    [ApiController]\n    [Route(\"api/[controller]\")]\n    public class TokenController : ControllerBase\n    {\n        private readonly ITokenService _tokenService;\n\n        public TokenController(ITokenService tokenService)\n        {\n            _tokenService = tokenService;\n        }\n\n        [HttpPost(\"create\")]\n        public IActionResult CreateToken([FromBody] TokenRequest request)\n        {\n            try\n            {\n                var token = _tokenService.CreateToken(request);\n                return Ok(new TokenResponse { Token = token, Success = true });\n            }\n            catch (Exception ex)\n            {\n                return BadRequest(new { Success = false, Error = ex.Message });\n            }\n        }\n\n        [HttpPost(\"validate\")]\n        public IActionResult ValidateToken([FromBody] TokenValidationRequest request)\n        {\n            var isValid = _tokenService.ValidateToken(request.Token);\n            return Ok(new { Success = isValid });\n        }\n    }\n}\n",
          }
        ]
      },
      {
        "type": "folder",
        "name": "Services",
        "items": [
          {
            "type": "file",
            "name": "ITokenService.cs",
            "code": "using TokenManagementSystem.Models;\n\nnamespace TokenManagementSystem.Services\n{\n    public interface ITokenService\n    {\n        string CreateToken(TokenRequest request);\n        bool ValidateToken(string token);\n    }\n}\n",
          },
          {
            "type": "file",
            "name": "TokenService.cs",
            "code": "using System;\nusing TokenManagementSystem.Models;\nusing TokenManagementSystem.Data;\nusing TokenManagementSystem.Utils;\n\nnamespace TokenManagementSystem.Services\n{\n    public class TokenService : ITokenService\n    {\n        private readonly ITokenRepository _repository;\n\n        public TokenService(ITokenRepository repository)\n        {\n            _repository = repository;\n        }\n\n        public string CreateToken(TokenRequest request)\n        {\n            // Construct token payload with user ID and a timestamp\n            var tokenPayload = $\"{request.UserId}:{DateTime.UtcNow.Ticks}\";\n            var token = SecurityHelper.Encrypt(tokenPayload);\n\n            var tokenModel = new Token\n            {\n                TokenValue = token,\n                UserId = request.UserId,\n                CreatedAt = DateTime.UtcNow,\n                ExpiresAt = DateTime.UtcNow.AddHours(1)\n            };\n\n            _repository.StoreToken(tokenModel);\n            return token;\n        }\n\n        public bool ValidateToken(string token)\n        {\n            var tokenModel = _repository.GetToken(token);\n            if (tokenModel == null || DateTime.UtcNow > tokenModel.ExpiresAt)\n            {\n                return false;\n            }\n            // Additional token integrity validations can be added here.\n            return true;\n        }\n    }\n}\n",
          }
        ]
      },
      {
        "type": "folder",
        "name": "Models",
        "items": [
          {
            "type": "file",
            "name": "Token.cs",
            "code": "using System;\n\nnamespace TokenManagementSystem.Models\n{\n    public class Token\n    {\n        public string TokenValue { get; set; }\n        public string UserId { get; set; }\n        public DateTime CreatedAt { get; set; }\n        public DateTime ExpiresAt { get; set; }\n    }\n}\n",
          },
          {
            "type": "file",
            "name": "TokenRequest.cs",
            "code": "namespace TokenManagementSystem.Models\n{\n    public class TokenRequest\n    {\n        public string UserId { get; set; }\n    }\n}\n",
          },
          {
            "type": "file",
            "name": "TokenResponse.cs",
            "code": "namespace TokenManagementSystem.Models\n{\n    public class TokenResponse\n    {\n        public bool Success { get; set; }\n        public string Token { get; set; }\n    }\n}\n",
          },
          {
            "type": "file",
            "name": "TokenValidationRequest.cs",
            "code": "namespace TokenManagementSystem.Models\n{\n    public class TokenValidationRequest\n    {\n        public string Token { get; set; }\n    }\n}\n",
          }
        ]
      },
      {
        "type": "folder",
        "name": "Data",
        "items": [
          {
            "type": "file",
            "name": "ITokenRepository.cs",
            "code": "using TokenManagementSystem.Models;\n\nnamespace TokenManagementSystem.Data\n{\n    public interface ITokenRepository\n    {\n        void StoreToken(Token token);\n        Token GetToken(string tokenValue);\n    }\n}\n",
          },
          {
            "type": "file",
            "name": "TokenRepository.cs",
            "code": "using System.Collections.Concurrent;\nusing TokenManagementSystem.Models;\n\nnamespace TokenManagementSystem.Data\n{\n    public class TokenRepository : ITokenRepository\n    {\n        private readonly ConcurrentDictionary<string, Token> _store = new ConcurrentDictionary<string, Token>();\n\n        public void StoreToken(Token token)\n        {\n            _store[token.TokenValue] = token;\n        }\n\n        public Token GetToken(string tokenValue)\n        {\n            _store.TryGetValue(tokenValue, out Token token);\n            return token;\n        }\n    }\n}\n",
          }
        ]
      },
      {
        "type": "folder",
        "name": "Utils",
        "items": [
          {
            "type": "file",
            "name": "SecurityHelper.cs",
            "code": "using System;\nusing System.Security.Cryptography;\nusing System.Text;\n\nnamespace TokenManagementSystem.Utils\n{\n    public static class SecurityHelper\n    {\n        public static string Encrypt(string plainText)\n        {\n            using var sha256 = SHA256.Create();\n            var bytes = Encoding.UTF8.GetBytes(plainText);\n            var hashBytes = sha256.ComputeHash(bytes);\n            var sb = new StringBuilder();\n            foreach (var b in hashBytes)\n            {\n                sb.Append(b.ToString(\"x2\"));\n            }\n            return sb.ToString();\n        }\n    }\n}\n",
          }
        ]
      }
    ]
  },
  "recommendedTags": [
    "Authentication",
    "Encryption"
  ]
}
""" + f"""
Now, generate a multi-folder, multi-file C# project structure for a digital bank code asset.
Asset Name: {asset_name}
Asset Description: {asset_description}\n\n
Available Tags (choose from these if applicable): {available_tags_str}\n\n
IMPORTANT: Do not generate any dummy code or placeholder implementations. Every file must have an actual, production-ready implementation with realistic business logic. Do not include comments indicating that the code is dummy or for testing purposes; instead, provide robust implementations suitable for a production digital bank environment. Do not include path in file name, just the name of file itself.\n\n
Return a JSON object with the keys 'projectStructure' and 'recommendedTags' following the provided schema.
"""

    messages = [
        {"role": "system", "content": "You are a helpful assistant that generates project structures as JSON."},
        {"role": "user", "content": user_message}
    ]
    print("call")
    # try:
    response = client.chat.completions.create(model="o3-mini",
    messages=messages,
    functions=[function_schema],
    function_call="auto",
    # max_tokens=800,
    # temperature=0.7
    )
    print("called")
    # The model will return a message with a function_call field
    message = response.choices[0].message
    # print(message)
    
    if message.function_call:
        print(message.function_call.arguments)
        arguments_str = message.function_call.arguments
        project_data = json.loads(arguments_str)
        return project_data
    else:
        # Fallback: try to parse the message content directly
        project_data = json.loads(message["content"])
        return project_data
    # except Exception as e:
    #     print(f"Error generating project structure for asset '{asset_name}': {e}")
    #     return None

def process_project_node(node, parent_id):
    """
    Recursively process a node from the generated project structure.
    Returns a tuple: (processed_node, primary_candidate)
    - processed_node: a dict in the FileSystemNode format.
    - primary_candidate: if this node is a file, it may serve as the primary code file;
      if not, then from a child.
    """
    node_type = node.get("type")
    if node_type == "folder":
        new_id = generate_guid()
        processed = {
            "Id": new_id,
            "Name": node.get("name"),
            "ParentId": parent_id,
            "Type": 0,  # Folder
            "Items": []
        }
        primary_candidate = None
        for child in node.get("items", []):
            child_processed, child_candidate = process_project_node(child, new_id)
            processed["Items"].append(child_processed)
            if primary_candidate is None and child_candidate is not None:
                primary_candidate = child_candidate
        return processed, primary_candidate
    elif node_type == "file":
        new_id = generate_guid()
        processed = {
            "Id": new_id,
            "Name": node.get("name"),
            "ParentId": parent_id,
            "Type": 1,  # CodeFile
            "Text": node.get("code"),
            "Language": 0  # C#
        }
        return processed, processed  # This file is a candidate for primary file.
    else:
        return None, None

def process_project_structure(project_structure, pre_generated_root_id):
    """
    Process the entire project structure returned by OpenAI.
    Uses pre_generated_root_id for the root folder.
    Returns a tuple: (root_folder_node, primary_file_node)
    """
    # Build the root folder node with our pre-generated GUID.
    root_folder = {
        "Id": pre_generated_root_id,
        "Name": project_structure.get("rootFolderName"),
        "ParentId": None,
        "Type": 0,  # Folder
        "Items": []
    }
    primary_candidate = None
    for node in project_structure.get("nodes", []):
        processed, candidate = process_project_node(node, pre_generated_root_id)
        root_folder["Items"].append(processed)
        if primary_candidate is None and candidate is not None:
            primary_candidate = candidate
    return root_folder, primary_candidate

def match_recommended_tags(recommended_tag_names, available_tags):
    """
    Given a list of recommended tag names (strings) and available_tags (list of dicts from CSV),
    return a list of tag objects (with Id and Name) that match (case-insensitive).
    """
    matched = []
    for tag_name in recommended_tag_names:
        for tag in available_tags:
            if tag["Name"].strip().lower() == tag_name.strip().lower():
                matched.append({"Id": tag["Id"], "Name": tag["Name"]})
                break
    return matched

# -------------------------------------------------------------------
# Load CSV data
# -------------------------------------------------------------------
assets = []
with open(ASSETS_CSV, "r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        assets.append({
            "Name": row["name"],
            "Description": row["description"]
        })

available_tags = []
with open(TAGS_CSV, "r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        available_tags.append({
            "Id": row["Id"],
            "Name": row["Name"],
            "Description": row["Description"]
        })

users = []
with open(USERS_CSV, "r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        users.append({
            "Id": row["Id"],
            "Name": row["Name"],
            "Email": row["Email"]
        })

# -------------------------------------------------------------------
# Process each asset and build JSON objects
# -------------------------------------------------------------------
code_assets = []
file_system_nodes = []
company_id = "DigitalBankCo"  # Static value for CompanyId

for asset in assets:
    asset_name = asset["Name"]
    asset_description = asset["Description"]

    # Generate GUIDs for the asset and its root folder.
    asset_id = generate_guid()
    root_folder_id = generate_guid()

    # Convert asset name to a valid folder name.
    folder_name = to_folder_name(asset_name)

    # Randomly assign a user from the users list.
    selected_user = random.choice(users)

    # Call OpenAI to generate the project structure (and recommended tags).
    project_data = generate_project_structure(asset_name, asset_description, available_tags)
    if project_data is None:
        print(f"Skipping asset '{asset_name}' due to generation error.")
        continue

    project_structure = project_data.get("projectStructure")
    recommended_tag_names = project_data.get("recommendedTags", [])
    root_folder_node, primary_file_node = process_project_structure(project_structure, root_folder_id)
    if primary_file_node is None:
        print(f"No primary file found for asset '{asset_name}', skipping asset.")
        continue

    # Build the PrimaryCodeFile object from the primary file node.
    primary_code_file = {
        "Id": primary_file_node["Id"],
        "Name": primary_file_node["Name"],
        "ParentId": primary_file_node["ParentId"],
        "Type": primary_file_node["Type"],
        "Text": primary_file_node["Text"],
        "Language": primary_file_node["Language"]
    }

    # Match recommended tags from OpenAI output against available tags.
    tag_objects = match_recommended_tags(recommended_tag_names, available_tags)

    # Build the CodeAsset object.
    code_asset = {
        "Id": asset_id,
        "CreatedById": selected_user["Id"],
        "CreatedDateUtc": datetime.datetime.utcnow().isoformat() + "Z",
        "IsDeleted": False,
        "LastModifiedById": None,
        "LastModifiedDateUtc": None,
        "Name": asset_name,
        "Description": asset_description,
        "Tags": tag_objects,
        "AssetType": 1,  # static enum value
        "Language": 0,   # static (C#)
        "RootFolderId": root_folder_id,
        "CompanyId": company_id,
        "PrimaryCodeFile": primary_code_file,
        "User": {
            "Id": selected_user["Id"],
            "Name": selected_user["Name"],
            "Email": selected_user["Email"]
        }
    }
    code_assets.append(code_asset)
    file_system_nodes.append(root_folder_node)

    # Save output after processing each asset.
    with open(CODE_ASSETS_JSON, "w", encoding="utf-8") as f:
        json.dump(code_assets, f, indent=2)
    with open(FILE_SYSTEM_NODES_JSON, "w", encoding="utf-8") as f:
        json.dump(file_system_nodes, f, indent=2)
    

# -------------------------------------------------------------------
# Write the output JSON files
# -------------------------------------------------------------------

print(f"Generated {len(code_assets)} code assets and {len(file_system_nodes)} file system nodes.")
